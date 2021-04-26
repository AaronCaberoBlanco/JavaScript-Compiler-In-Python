class GCO:

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

    def __init__(self, ci_out_fd, ci, size_RAs, TS_):
        self.ci = ci
        self.ci_out_fd = ci_out_fd
        self.size_RAs = size_RAs
        self.TS = TS_

    # Antes de llamar a generate_co se incian todas las globales con RES XXX y se apunta IY al primer elemento
    def generate_co(self):
        res = []
        for quartet in self.ci:
            res = self.process_quartet(quartet) + res
        return res

    def process_quartet(self, quartet):
        res = []
        match quartet[0]:
            case 10: #EL=   #It supposes global variable, based on input
                res = [(None,'MOVE',f'#{quartet[1][1]}','.R1')]   #Problema aquí con el segundo elemento (tupla)  TS/Literal
                res = [(None,'MOVE','IY','.R2')] + res
                desp = self.TS.get_attribute(0,1, self.ATTR_DESP)
                res = [(None,'ADD','.R2',f'#{desp}') if desp > 0 else ''] + res
                res = [(None,'MOVE','A','.R2')] + res
                res = [(None,'MOVE','.R1','[.R2]')] + res
        return res

    # -----------------------------------------Print methods-----------------------------------------

    def print_co(self, co):
        """Prints object code to a file.

        Prints the co to the output fd specified in the class

        Args:
            co (List): A list containing tuples like (add, .R2, .R3, ;comm). None not allowed
        """
        res = ''
        for inst in co:
            res = self.format_tuple(inst) + res
        with open(self.ci_out_fd, 'w') as out_fd:
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
                    res += f'{elem} '
            return f'{res[:-1]}\n'
        else:
            return ''