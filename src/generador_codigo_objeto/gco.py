import re
from src.analizador_sintactico_y_semantico.js_parser import JSParser


class GCO:
    REG_AUX = '.R9'
    REG_RET = '.R8'

    def __init__(self, co_out_fd, ci, size_RAs_, TS_):
        self.ci = ci
        self.param_counter = 1                          #param_counter is reset everytime oper=call because it implies all the params have been already copied
        self.co_out_fd = co_out_fd
        self.size_RAs = size_RAs_
        self.TS = TS_
        self.n_copy = 0
        self.lista_cadenas = []
        self.curr_func_size_RA = ''
        self.ret_addr_counter = 0
        self.last_inst = ''

    # Después de llamar a generate_co se inician todas las globales con RES XXX y se apunta IY al primer elemento
    def convert_co(self):
        result = []
        result += self.inst_init()
        for quartet in self.ci:
            if len(quartet) == 1 and type(quartet[0]) is str:
                result += quartet,
                if re.search('.*fin.*funciones.*', quartet[0], re.IGNORECASE):
                    result += [('; Inicio de código del main',)] + \
                              [('main:', 'NOP', None, None, None)]
                    self.curr_func_size_RA = 'tamRAFunMain'
            else:
                result += self.quartet_CI_to_CO(quartet)
        result += self.inst_end()
        return result

    def inst_init(self):
        result = [(None, 'ORG', 0, None, None)] + \
                 [(None, 'MOVE', '#beginED', '.IY', None)] + \
                 [(None, 'MOVE', '#beginStack', '.IX', None)] + \
                 ['\n'] + \
                 [(None, 'BR', '/main', None, None)]  # IX apunta al valor anterior (beforefirst)
        return result

    def inst_end(self): #RES 0 causes other instruction to override HALT when size_main_RA is 0.
        size_main_RA = self.size_RAs['tamRAFunMain'] + (1 if self.size_RAs['tamRAFunMain'] == 0 else 0)
        result = [(None, 'HALT', None, None, None)] + \
                 [('; Fin de código del main',)] + \
                 self.book_space_size_RA() + \
                 ['\n'] + \
                 [('beginED:', 'RES', size_main_RA, None, None)] + \
                 self.book_space_cad() + \
                 ['\n'] + \
                 [('beginStack:', 'NOP', None, None, None)] + \
                 [(None, 'END', None, None, None)]
        return result

    def book_space_size_RA(self):
        result = []
        for etiq_fun, size_RA_fun in self.size_RAs.items():
            result +=[(f'{etiq_fun}:', 'EQU', size_RA_fun , None, None)]

        return result

    def string_to_label(self, str_):
        str_removed_symbols=re.sub('[^a-zA-Z0-9]', '', str_[1:-1])
        return str_removed_symbols[:4]

    def book_space_cad(self):
        result = []
        for i, str_ in enumerate(self.lista_cadenas):
            result += [(f'cad{i}_{self.string_to_label(str_)}:', 'DATA', str_, None, None)]
        return result

    def quartet_CI_to_CO(self, quartet):
        oper = quartet[0]
        op1 = quartet[1]
        op2 = quartet[2]
        res = quartet[3]

        inst_list = []
        oper_ = self.get_key_from_value(oper, JSParser.OPERATOR_CODE)
        match oper_:
            case '=EL':
                # TODO: rehacer/quitar muchos comentarios para que no se dupliquen con los implementados en store_in_reg
                inst_list += self.store_in_reg(op1, '.R1', 'Value') +\
                             self.store_in_reg(res, '.R3', 'Dir') +\
                             [(None, 'MOVE', '.R1', '[.R3]')]
            case '=Cad':  # (11, (4, "Hola"), None, (1, 2)) --- (11, (2,4), None, (1, 2))
                inst_list += self.store_in_reg(op1, '.R1', 'Dir') + \
                             self.store_in_reg(res, '.R3', 'Dir') + \
                             self.copy_str('.R1', '.R3')
            case '=and':  # (12, (1,2), (1,3), (1,4))
                inst_list += self.store_in_reg(op1, '.R1', 'Value') + \
                             self.store_in_reg(op2, '.R2', 'Value') + \
                             self.store_in_reg(res, '.R3', 'Dir') + \
                             [(None, 'AND', '.R1', '.R2', None)] + \
                             [(None, 'MOVE', '.A', '[.R3]', None)]
            case '=-':
                inst_list += self.store_in_reg(op1, '.R1', 'Value') + \
                             self.store_in_reg(op2, '.R2', 'Value') + \
                             self.store_in_reg(res, '.R3', 'Dir') + \
                             [(None, 'SUB', '.R1', '.R2', None)] + \
                             [(None, 'MOVE', '.A', '[.R3]', None)]
            case ':':
                label = op1[1]
                inst_list += [(f'{label[1:]}:', 'NOP', None, None, None)]
                if re.search('.*EtiqFun.*', label, re.IGNORECASE):
                    self.curr_func_size_RA = label.replace('#Etiq', 'tamRA', 1)
            case 'goto':
                inst_list += [(None, 'BR', f'/{res[1][1:]}', None, None)]
            case 'if=goto':
                inst_list += self.store_in_reg(op1, '.R1', 'Value') + \
                             self.store_in_reg(op2, '.R2', 'Value') + \
                             [(None, 'CMP', '.R1', '.R2', None)] + \
                             [(None, 'BZ', f'/{res[1][1:]}', None, None)]

            case param_matched if re.search('param.*', param_matched):
                inst_list += self.store_in_reg(op1, '.R1', 'Dir') +\
                             [(None, 'ADD', f'#{self.size_RAs[self.curr_func_size_RA]}', '.IX', None)] +\
                             [(None, 'ADD', f'#{self.param_counter}', '.A', None)]

                if param_matched == 'paramEL':
                    inst_list += [(None, 'MOVE', '[.R1]', '[.A]', None)]
                    self.param_counter += 1
                elif param_matched == 'paramCad':
                    inst_list += [(None, 'MOVE', '.A', '.R3', None)] + self.copy_str('.R1','.R3')
                    self.param_counter += 64

            case call_matched if re.search('call.*', call_matched):
                self.param_counter = 1

                ret_addr = f"{op1[1].replace('#Etiq', f'dirRet{self.ret_addr_counter}_', 1)}"
                size_RA = self.curr_func_size_RA
                etiq_fun = op1[1][1:]   #Comentario de sección -> [('; Secuencia de llamada',)]
                inst_list += [('; Secuencia de llamada',)] + \
                             ['; Almacenamiento de dir. retorno'] + \
                             [(None, 'ADD', f'#{size_RA}', '.IX',None)] + \
                             [(None, 'MOVE', f'#{ret_addr}', '[.A]', None)] + \
                             ['; Actualizacion de puntero de pila'] + \
                             [(None, 'ADD', f'#{size_RA}', '.IX', None)] + \
                             [(None, 'MOVE', '.A', '.IX', None)] + \
                             [(None, 'BR', f'/{etiq_fun}', None, None)] + \
                             [('; Secuencia de retorno',)] + \
                             [(f'{ret_addr}:', 'NOP', None, None, None)] + \
                             ['; Restauracion de puntero de pila'] + \
                             [(None, 'SUB', '.IX', f'#{size_RA}', None)] + \
                             [(None, 'MOVE', '.A', '.IX', None)]

                if call_matched != 'callVoid':
                    if call_matched == 'callValueCad':
                        inst_list += self.store_in_reg(res, '.R3', 'Dir','; Copia de valor devuelto') + \
                                     self.copy_str(self.REG_RET, '.R3')
                    elif call_matched == 'callValueEL':
                        inst_list += self.store_in_reg(res, '.R3', 'Dir','; Copia de valor devuelto') + \
                                     [(None, 'MOVE', self.REG_RET, '[.R3]', None)]

                self.ret_addr_counter += 1
            case 'returnVoid':
                inst_list += [(None, 'BR', '[.IX]', None, None)]
            case 'returnEL':
                inst_list += self.store_in_reg(op1, self.REG_RET, 'Value', f'; Valor a devolver en {self.REG_RET}') + \
                             ['\n'] + \
                             [(None, 'BR', '[.IX]', None, None)]
            case 'returnCad':
                inst_list += self.store_in_reg(op1, self.REG_RET, 'Dir', f'; Direccion de la cadena a devolver en {self.REG_RET}') + \
                             ['\n'] + \
                             [(None, 'BR', '[.IX]', None, None)]
            case 'alertEnt':
                inst_list += self.store_in_reg(op1, self.REG_AUX, 'Value') +\
                             ['\n'] + \
                             [(None, 'WRINT', self.REG_AUX, None, None)]
            case 'alertCad':
                inst_list += self.store_in_reg(op1, self.REG_AUX, 'Dir') + \
                             ['\n'] + \
                             [(None, 'WRSTR', f'[{self.REG_AUX}]', None, None)]
            case 'inputEnt':
                inst_list += self.store_in_reg(res, self.REG_AUX, 'Dir') + \
                             ['\n'] + \
                             [(None, 'ININT', f'[{self.REG_AUX}]', None, None)]
            case 'inputCad':
                inst_list += self.store_in_reg(res, self.REG_AUX, 'Dir') + \
                             ['\n'] + \
                             [(None, 'INSTR', f'[{self.REG_AUX}]', None, None)]

        return inst_list

    def store_in_reg(self, oper, reg, mode, comment=None):
        """
        [10, (3, 2), , (1, 1)]
        get_operand((3, 2)) --> MOVE #2,.R1
        get_operand((1, 4)) --> ADD .IY,#4
                                MOVE .A,{self.REG_AUX}
                                MOVE [.{self.REG_AUX}],.R3

        """
        result = [f'{comment}'] if comment is not None else []      #Comentario de bloque
        oper_ = self.get_key_from_value(oper[0], JSParser.OPERAND_CODE)
        match oper_:
            case 'global':  # Global
                desp = oper[1]
                if mode == 'Value':
                    result += [f'\t; Almacenamiento del valor de una variable global en {reg}'] + \
                              [(None, 'ADD', f'#{desp}', '.IY', None)] +\
                              [(None, 'MOVE', '.A', f'{self.REG_AUX}', None)] +\
                              [(None, 'MOVE', f'[{self.REG_AUX}]', reg, None)]
                elif mode == 'Dir':
                    result += [f'\t; Almacenamiento de la direccion de una variable global en {reg}'] + \
                              [(None, 'ADD', f'#{desp}', '.IY', None)] +\
                              [(None, 'MOVE', '.A', reg, None)]
            case 'local': # VL + DT + P
                desp = oper[1] + 1 #Se suma 1 para pasar por encima del EM
                if mode == 'Value':
                    result += [f'\t; Almacenamiento del valor de una variable local en {reg}'] + \
                              [(None, 'ADD', f'#{desp}','.IX', None)] +\
                              [(None, 'MOVE', '.A', f'{self.REG_AUX}', None)] +\
                              [(None, 'MOVE', f'[{self.REG_AUX}]', reg, None)]
                elif mode == 'Dir':
                    result += [f'\t; Almacenamiento del valor de la direccion de una variable local en {reg}'] + \
                              [(None, 'ADD', f'#{desp}', '.IX', None)] +\
                              [(None, 'MOVE', '.A', reg, None)]
            case 'ent':
                if mode == 'Value':
                    literal = oper[1]
                    result +=  [(None, 'MOVE', f'#{literal}', reg, None)]
            case 'cad':
                if mode == 'Dir':
                    str_ = oper[1]
                    result += [(None, 'MOVE', f'#cad{len(self.lista_cadenas)}_{self.string_to_label(str_)}', reg, None)]
                    self.lista_cadenas.append(str_)

        return result

    def copy_str(self, r_sour, r_dest):
        result = [('; Inicio bucle de copia de cadena',)] + \
                 [(f'copia{self.n_copy}:', 'NOP', None, None, None)] + \
                 [(None, 'MOVE', f'[{r_sour}]', self.REG_AUX, None)] + \
                 [(None, 'MOVE', f'{self.REG_AUX}', f'[{r_dest}]', None)] + \
                 [(None, 'ADD', '#1', r_sour, None)] + \
                 [(None, 'MOVE', '.A', r_sour, None)] + \
                 [(None, 'ADD', '#1', r_dest, None)] + \
                 [(None, 'MOVE', '.A', r_dest, None)] + \
                 [(None, 'CMP', '#0', f'{self.REG_AUX}', None)] + \
                 [(None, 'BNZ', f'/copia{self.n_copy}', None, None)] + \
                 [('; Fin bucle de copia de cadena',)]
        self.n_copy += 1
        return result

    def get_key_from_value(self, val, dict_):
        for key, value in dict_.items():
            if val == value:
                return key

    # -----------------------------------------Print methods-----------------------------------------
    #   Standard procedure to generate comments in .ens file
    #   There are 3 type of comments:
    #       [(";-------- I'm a section comment",)] -> \t\t indentation and \n top or bottom
    #       ["; I'm a block comment"] -> \t\t\t indentation and \n
    #       ['Etiq','ADD', '.R0', '.R5', '; I'm a in-line comment'] -> No indentation nor \n
    # -----------------------------------------------------------------------------------------------

    def print_co(self):
        """Prints object code to a file.

        Prints the co to the output fd specified in the class
        """
        # Args:
        #     co (List): A list containing tuples like (etiq_ens, add, .R2, .R3, ;comm). None not allowed

        co = self.convert_co()
        result = ''
        for inst in co:
            if type(inst) is tuple and len(inst) < 2:
                result += self.get_processed_comment(inst[0], 'section')
            elif type(inst) is str:
                result += self.get_processed_comment(inst,'block')
            else:
                self.last_inst = self.format_inst(inst)
                result += self.last_inst


        print(result, file=self.co_out_fd)

    def format_inst(self, inst):
        """Formats the tuple given into a printable string

           Returns the string formatted

        Args:
           inst (Tuple): A tuple made up of 5 items: etiq, oper, op1, op2, comment. All elements can be null except the second one.
        """
        if len(inst) > 0:
            res_inst = inst[0] if inst[0] is not None else ''
            res_inst += f'{self.get_blank_space(inst[0])} {inst[1]} '
            for count, sub_inst in enumerate(inst[2:4], 2):
                res_inst += f' {sub_inst},' if sub_inst is not None else ''
            res_inst = res_inst[:-1]
            res_inst += f' {inst[4]}' if len(inst) > 4 and inst[4] is not None else ''
            return f'{res_inst}\n' if self.last_inst != f'{res_inst}\n' and 'BR [.IX]' != res_inst else ''
        return ''

    def get_blank_space(self, etiq):
        if etiq is None:
            return ' ' *20
        return ' ' * (20 - len(etiq))

    def get_processed_comment(self, comment_, type):
        comment = re.sub('[\n]*', '', comment_)
        if type == 'section':
            comment = re.sub('[\t]*', '', comment)
            match comment:      #TODO: IF No entiendo
                case comment if re.search('Inicio.* funcion.*', comment):
                    comment = f'\n\t{comment}'
                case comment if re.search('Inicio.*', comment):
                    comment = f'\n\t\t{comment}'
                case comment if re.search('Fin.*', comment):
                    comment = f'\t\t{comment}\n'
                case comment if re.search('Secuencia.*', comment):
                    comment = f'\n\t\t{comment}'
        elif type == 'block':
            comment = f"\t\t\t{comment}"
        return f'{comment}\n'