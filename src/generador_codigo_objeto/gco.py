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

    # Después de llamar a generate_co se inician todas las globales con RES XXX y se apunta IY al primer elemento
    def convert_co(self):
        result = []
        result += self.inst_init()
        for quartet in self.ci:
            if len(quartet) == 1 and type(quartet[0]) is str:
                result += quartet,
                if re.search('.*fin.*funciones.*', quartet[0], re.IGNORECASE):
                    result += [('\n\t; Inicio de código del main',)] + \
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
                 [(None, 'BR', '/main', None, None)]  # IX apunta al valor anterior (beforefirst)
        return result

    def inst_end(self): #RES 0 causes other instruction to override HALT when size_main_RA is 0.
        size_main_RA = self.size_RAs['tamRAFunMain'] + (1 if self.size_RAs['tamRAFunMain'] == 0 else 0)
        result = [(None, 'HALT', None, None, '\n\n\t; Fin de código del main\n')] + \
                 self.book_space_size_RA() +\
                 [('beginED:', 'RES', size_main_RA, None, None)] + \
                 self.book_space_cad() + \
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
            case '=EL':  # (10, (3,1), None, (2,3))
                inst_list += self.store_in_reg(op1, '.R1', 'Value', '; Valor de Oper1 en R1') +\
                             self.store_in_reg(res, '.R3', 'Dir', '; Direccion de Res en R3') +\
                             [(None, 'MOVE', '.R1', '[.R3]', '; Valor de Oper1(R1) a Res(direccion a donde apunta R3)')]
            case '=Cad':  # (11, (4, "Hola"), None, (1, 2)) --- (11, (2,4), None, (1, 2))
                inst_list += self.store_in_reg(op1, '.R1', 'Dir') + \
                             self.store_in_reg(res, '.R3', 'Dir') + \
                             self.copy_str('.R1', '.R3')
            case '=and':  # (12, (1,2), (1,3), (1,4))
                inst_list += self.store_in_reg(op1, '.R1', 'Value', '; Valor de Oper1 en R1') + \
                             self.store_in_reg(op2, '.R2', 'Value', '; Valor de Oper2 en R2') + \
                             self.store_in_reg(res, '.R3', 'Dir', '; Dirección de Res en R3') + \
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
                             [(None, 'ADD', f'#{self.param_counter}', '.A', '; .A contiene la dirección del parametro alojado en el RA')]

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
                etiq_fun = op1[1][1:]
                inst_list += [('; Secuencia de llamada',)] + \
                             [(None, 'ADD', f'#{size_RA}', '.IX',None)] + \
                             [(None, 'MOVE', f'#{ret_addr}', '[.A]', None)] + \
                             [(None, 'ADD', f'#{size_RA}', '.IX', None)] + \
                             [(None, 'MOVE', '.A', '.IX', None)] + \
                             [(None, 'BR', f'/{etiq_fun}', None, None)] + \
                             [('; Secuencia de retorno',)] + \
                             [(f'{ret_addr}:', 'NOP', None, None, None)] + \
                             [(None, 'SUB', '.IX', f'#{size_RA}', None)] + \
                             [(None, 'MOVE', '.A', '.IX', None)]

                if call_matched != 'callVoid':
                    if call_matched == 'callValueCad':
                        inst_list += self.store_in_reg(res, '.R3', 'Dir') + \
                                     self.copy_str(self.REG_RET, '.R3')
                    elif call_matched == 'callValueEL':
                        inst_list += self.store_in_reg(res, '.R3', 'Dir') + \
                                     [(None, 'MOVE', self.REG_RET, '[.R3]', None)]

                self.ret_addr_counter += 1
            case 'returnVoid':
                inst_list += [(None, 'BR', '[.IX]', None, None)]
            case 'returnEL':
                inst_list += self.store_in_reg(op1, self.REG_RET, 'Value', f';Valor a devolver en {self.REG_RET}') + \
                             [(None, 'BR', '[.IX]', None, None)]
            case 'returnCad':
                inst_list += self.store_in_reg(op1, self.REG_RET, 'Dir', f';Direccion de la cadena a devolver en {self.REG_RET}') + \
                             [(None, 'BR', '[.IX]', None, None)]
            case 'alertEnt':
                inst_list += self.store_in_reg(op1, self.REG_AUX, 'Value') +\
                             [(None, 'WRINT', self.REG_AUX, None, None)]
            case 'alertCad':
                inst_list += self.store_in_reg(op1, self.REG_AUX, 'Dir') + \
                             [(None, 'WRSTR', f'[{self.REG_AUX}]', None, None)]
            case 'inputEnt':
                inst_list += self.store_in_reg(res, self.REG_AUX, 'Dir') + \
                             [(None, 'ININT', f'[{self.REG_AUX}]', None, None)]
            case 'inputCad':
                inst_list += self.store_in_reg(res, self.REG_AUX, 'Dir') + \
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
        result = [(f'\n\t\t\t\t{comment}\n',)] if comment is not None else []
        oper_ = self.get_key_from_value(oper[0], JSParser.OPERAND_CODE)
        match oper_:
            case 'global': # Global
                desp = oper[1]
                if mode == 'Value':
                    result += [(None, 'ADD', f'#{desp}', '.IY', None)] +\
                              [(None, 'MOVE', '.A', f'{self.REG_AUX}', None)] +\
                              [(None, 'MOVE', f'[{self.REG_AUX}]', reg, None)]
                elif mode == 'Dir':
                    result += [(None, 'ADD', f'#{desp}', '.IY', None)] +\
                              [(None, 'MOVE', '.A', reg, None)]
            case 'local': # VL + DT + P
                desp = oper[1] + 1 #Se suma 1 para pasar por encima del EM
                if mode == 'Value':
                    result += [(None, 'ADD', f'#{desp}','.IX', None)] +\
                              [(None, 'MOVE', '.A', f'{self.REG_AUX}', None)] +\
                              [(None, 'MOVE', f'[{self.REG_AUX}]', reg, None)]
                elif mode == 'Dir':
                    result += [(None, 'ADD', f'#{desp}', '.IX', None)] +\
                              [(None, 'MOVE', '.A', reg, None)]
            case 'ent':  # Literal (EL)
                if mode == 'Value':
                    literal = oper[1]
                    result +=  [(None, 'MOVE', f'#{literal}', reg, None)]
            case 'cad': # Cad
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

    def print_co(self, co):
        """Prints object code to a file.

        Prints the co to the output fd specified in the class

        Args:
            co (List): A list containing tuples like (etiq_ens, add, .R2, .R3, ;comm). None not allowed
        """
        result = ''
        for inst in co:
            if len(inst) == 1 and type(inst) is str:
                inst = inst[(1 if inst[0] == '\n' else 0):]
                result += f' \n\t\t {inst}\n'
            else:
                result += self.format_inst(inst)

        print(result, file=self.co_out_fd)

    def format_inst(self, inst):
        """Formats the tuple given into a printable string

           Returns the string formatted

        Args:
           inst (Tuple): A tuple made up of 5 items: etiq, oper, op1, op2, comment. All elements can be null except the second one.
        """
        if len(inst) > 0:
            res_inst = inst[0] if inst[0] is not None else ''
            if len(inst) < 2 :
                if  len(res_inst) == 0:
                    return ''
                res_inst = res_inst[(1 if res_inst[0] == '\n' else 0):]
                res_inst += self.get_blank_space(None)
                return f' \n\t\t {res_inst} \n'
            elif len(inst) != 5:
                return f' \n\t\t {res_inst} \n'
            res_inst += f'{self.get_blank_space(inst[0])} {inst[1]} '
            for count, sub_inst in enumerate(inst[2:4], 2):
                res_inst += f' {sub_inst},' if sub_inst is not None else ''
            res_inst = res_inst[:-1]
            res_inst += f' {inst[4]}' if len(inst) > 4 and inst[4] is not None else ''
            return f'{res_inst}\n'
        return ''

    def get_blank_space(self, etiq):
        if etiq is None:
            return ' ' *20
        return ' ' * (20 - len(etiq))
