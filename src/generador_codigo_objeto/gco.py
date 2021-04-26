class GCO:
    #TODO: Crear fichero con finales globales
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

    # Después de llamar a generate_co se inician todas las globales con RES XXX y se apunta IY al primer elemento
    def convert_co(self):
        res = []
        for quartet in self.ci:
            if len(quartet) == 1 and type(quartet[0]) is str:
                res += quartet  # Comment in ens
            else:
                res += self.convert_quartet(quartet)
        return res

    def convert_quartet(self, quartet):
        res = []
        match quartet[0]:
            case 10:  # (10, (3,1), None, (2,3)) --- (10, (1,1), None
                res += self.set_registry(quartet[1], '.R1', 'Value')
                res += self.set_registry(quartet[3], '.R3', 'Dir')
                res += [(None, 'MOVE', '.R1', '[.R3]', '\n')]
            case 11:  # (11, (4, "Hola"), None, (1, 2)) --- (11, (2,4), None, (1, 2))
                ...    #etiq DATA 123
            case 12:  # (12, (1,2), (1,3), (1,4))
                res += self.set_registry(quartet[1], '.R1', 'Value')
                res += self.set_registry(quartet[2], '.R2', 'Value')
                res += self.set_registry(quartet[3], '.R3', 'Dir')
                res += [(None, 'AND', '.R1', '.R2', None)]
                res += [(None, 'MOVE', '.A', '[.R3]', '\n')]

        return res


    def set_registry(self, oper, reg, mode, comment=None):
        """
        [10, (3, 2), , (1, 1)]
        get_operand((3, 2)) --> MOVE #2,.R1
        get_operand((1, 4)) --> ADD .IY,#4
                                MOVE .A,{self.REG_AUX}
                                MOVE [.{self.REG_AUX}],.R3

        """
        res = []
        match oper[0]:
            case 1: # Global
                desp = oper[1]
                if mode == 'Value':
                    res += [(None, 'ADD', f'#{desp}', '.IY', None)]
                    res += [(None, 'MOVE', '.A', f'{self.REG_AUX}', None)]
                    res += [(None, 'MOVE', f'[{self.REG_AUX}]', reg, None)]
                elif mode == 'Dir':
                    res += [(None, 'ADD', f'#{desp}', '.IY', None)]
                    res += [(None, 'MOVE', '.A', reg, None)]
            case 2: # VL + DT + P
                desp = oper[1]
                if mode == 'Value':
                    res += [(None, 'ADD', f'#{desp}','.IX', None)]
                    res += [(None, 'MOVE', '.A', f'{self.REG_AUX}', None)]
                    res += [(None, 'MOVE', f'[{self.REG_AUX}]', reg, None)]
                elif mode == 'Dir':
                    res += [(None, 'ADD', f'#{desp}', '.IX', None)]
                    res += [(None, 'MOVE', '.A', reg, None)]
            case 3:  # Literal (EL)
                literal = oper[1]
                res +=  [(None, 'MOVE', f'#{literal}', reg, None)]
            case 4: # Cad
                pass
        return res

    # -----------------------------------------Print methods-----------------------------------------

    def print_co(self, co):
        """Prints object code to a file.

        Prints the co to the output fd specified in the class

        Args:
            co (List): A list containing tuples like (etiq_ens, add, .R2, .R3, ;comm). None not allowed
        """
        res = ''
        for inst in co:
            if len(inst) == 1 and type(inst[0]) is str:  # Comments
                res += f'{inst[0]}\n'
            else:
                res += self.format_tuple(inst)
        with open(self.co_out_fd, 'w') as out_fd:
            print(res, file=out_fd)

    def format_tuple(self, tuple_):
        """Formats the tuple given into a printable string

           Returns the string formatted

        Args:
           tuple_ (Tuple): A tuple made up of 5 items: etiq, oper, op1, op2, comment. All elements can be null except the second one.
        """
        if len(tuple_) > 0:
            res = '\t' if tuple_[0] is None else ''
            for elem in tuple_:
                if elem is not None:
                    res += f'{elem}, '
            return f'{res[:-2]}\n'
        else:
            return ''