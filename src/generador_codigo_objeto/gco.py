import re

class GCO:
    OPERAND_CODE = {
        'global': 1,
        'local': 2,
        'valor': 2,
        'tmp': 2,
        'ent': 3,
        'cad': 4,
        'etiq': 5
    }
    OPERATOR_CODE = {
        '=EL': 10,
        '=Cad': 11,
        '=and': 12,
        '=-': 13,
        ':': 14,
        'goto': 15,
        'if=goto': 16,
        'paramEL': 17,
        'paramCad': 18,
        'callValueEL': 19,
        'callValueCad': 20,
        'callVoid': 21,
        'returnVoid': 22,
        'returnEL': 23,
        'returnCad': 24,
        'alertEnt': 25,
        'alertCad': 26,
        'inputEnt': 27,
        'inputCad': 28
    }

    ATTR_TYPE = 'Tipo'
    ATTR_LEXEM = 'LEXEMA'
    ATTR_DESP = 'Despl'
    ATTR_LABEL = 'EtiqFuncion'
    ATTR_NUM_PARAMS = 'NumParam'
    ATTR_TYPE_PARAMS = 'TipoParam'
    ATTR_RETURN_VALUE = 'TipoRetorno'

    FUNCTION_TYPE = 'funcion'
    LOG_TYPE = 'logico'
    INT_TYPE = 'entero'
    STRING_TYPE = 'cadena'
    VOID_TYPE = 'void'

    REG_AUX = '.R9'

    def __init__(self, co_out_fd, ci, size_RAs_, TS_):
        self.ci = ci
        self.co_out_fd = co_out_fd
        self.size_RAs = size_RAs_
        self.TS = TS_
        self.n_copy = 0
        self.lista_cadenas = []

    # Después de llamar a generate_co se inician todas las globales con RES XXX y se apunta IY al primer elemento
    def convert_co(self):
        res = []
        res += self.inst_init()
        for quartet in self.ci:
            if len(quartet) == 1 and type(quartet[0]) is str:
                res += quartet,
                if re.match('.*fin.*funcion.*', quartet[0], re.IGNORECASE):
                    res += [('\n\t; Inicio de código del main',)]
                    res += [('main:', 'NOP', None, None,None)]
            else:
                res += self.convert_quartet(quartet)
        res += self.inst_end()
        return res

    def inst_init(self):
        result = []
        result += [(None, 'ORG', 0, None, None)]
        result += [(None, 'MOVE', 'beginED', '.IY', None)]
        result += [(None, 'Move', 'beginStack', '.IX', None)] # IX apunta al valor anterior (beforefirst)
        result += [(None, 'BR', '/main', None, None)]
        return result

    def inst_end(self):
        result = [(None, 'HALT', None, None, '\n\t; Fin de código del main')]
        result += [('beginED:', 'RES', self.size_RAs['#main'], None, None)]
        self.book_space_cad()
        result += [('beginStack:', 'NOP', None, None, None)]
        result += [(None, 'END', None, None, None)]
        return result

    def book_space_cad(self):
        result = []
        for i, str_ in enumerate(self.lista_cadenas):
            result += [(f'cad{i}_{str_[0:4]}:', 'DATA', str_)]
        return result

    def convert_quartet(self, quartet):
        oper = quartet[0]
        op1 = quartet[1]
        op2 = quartet[2]
        res = quartet[3]

        inst_list = []

        match oper:
            case 10:  # (10, (3,1), None, (2,3)) --- (10, (1,1), None
                inst_list += self.set_registry(op1, '.R1', 'Value', '; Carga el valor')
                inst_list += self.set_registry(res, '.R3', 'Dir', '; Carga en la dirección')
                inst_list += [(None, 'MOVE', '.R1', '[.R3]', '\n')]
            case 11:  # (11, (4, "Hola"), None, (1, 2)) --- (11, (2,4), None, (1, 2))
                ...    #etiq DATA 123
            case 12:  # (12, (1,2), (1,3), (1,4))
                inst_list += self.set_registry(op1, '.R1', 'Value','; Carga true en R1')
                inst_list += self.set_registry(op2, '.R2', 'Value','; Carga false en R2')
                inst_list += self.set_registry(res, '.R3', 'Dir','; Dirección donde se almacena el resultado')
                inst_list += [(None, 'AND', '.R1', '.R2', None)]
                inst_list += [(None, 'MOVE', '.A', '[.R3]', '\n')]

        return inst_list


    def set_registry(self, oper, reg, mode, comment=None):
        """
        [10, (3, 2), , (1, 1)]
        get_operand((3, 2)) --> MOVE #2,.R1
        get_operand((1, 4)) --> ADD .IY,#4
                                MOVE .A,{self.REG_AUX}
                                MOVE [.{self.REG_AUX}],.R3

        """
        result = [(f'\n\t{comment}\n',)] if comment is not None else []
        match oper[0]:
            case 1: # Global
                desp = oper[1]
                if mode == 'Value':
                    result += [(None, 'ADD', f'#{desp}', '.IY', None)]
                    result += [(None, 'MOVE', '.A', f'{self.REG_AUX}', None)]
                    result += [(None, 'MOVE', f'[{self.REG_AUX}]', reg, None)]
                elif mode == 'Dir':
                    result += [(None, 'ADD', f'#{desp}', '.IY', None)]
                    result += [(None, 'MOVE', '.A', reg, None)]
            case 2: # VL + DT + P
                desp = oper[1]
                if mode == 'Value':
                    result += [(None, 'ADD', f'#{desp}','.IX', None)]
                    result += [(None, 'MOVE', '.A', f'{self.REG_AUX}', None)]
                    result += [(None, 'MOVE', f'[{self.REG_AUX}]', reg, None)]
                elif mode == 'Dir':
                    result += [(None, 'ADD', f'#{desp}', '.IX', None)]
                    result += [(None, 'MOVE', '.A', reg, None)]
            case 3:  # Literal (EL)
                literal = oper[1]
                result +=  [(None, 'MOVE', f'#{literal}', reg, None)]
            case 4: # Cad
                str_ = oper[1]
                result += [(None, 'MOVE', f'/cad{len(self.lista_cadenas)}_{str_[0:4]}', reg),None]
                self.lista_cadenas.append(str_)
        return result

    def copy_loop(self, r_sour, r_dest):
        result = [('; Inicio bucle de copia',)] +\
            [(f'copia{self.n_copy}:' 'NOP', None, None, None)] +\
            [(None, 'MOVE', f'[{r_sour}]', self.REG_AUX, None)] +\
            [(None, 'MOVE', f'[{self.REG_AUX}]', f'[{r_dest}]', None)] +\
            [(None, 'ADD', '#1', r_sour, None)] +\
            [(None, 'MOVE', '.A', r_sour, None)] +\
            [(None, 'ADD', '#1', r_dest, None)] +\
            [(None, 'MOVE', '.A', r_dest, None)] +\
            [(None, 'CMP', '#\0', f'{self.REG_AUX}', None)] +\
            [(None, 'BZ', f'/copia{self.n_copy}:', None, None)] +\
            [('; Inicio bucle de copia',)]
        return result


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
                result += f'{inst}\n'
            else:
                result += self.format_tuple(inst)
        with open(self.co_out_fd, 'w') as out_fd:
            print(result, file=out_fd)

    def format_tuple(self, tuple_):
        """Formats the tuple given into a printable string

           Returns the string formatted

        Args:
           tuple_ (Tuple): A tuple made up of 5 items: etiq, oper, op1, op2, comment. All elements can be null except the second one.
        """
        if len(tuple_) > 0:
            result = '\t' if tuple_[0] is None else ''
            for i, elem in enumerate(tuple_):
                if elem is not None:
                    result += f'{elem}, ' if i > 1 else f'{elem} '
            return f'{result[:-2]}\n'
        else:
            return ''