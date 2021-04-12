import sys
import builtins

from sly import Parser

from src.analizador_lexico.js_lexer import JSLexer

''' Para propagar toda la información del GCI sin dañar a la existente del semántico. Indexamos las cosas del GCI al final
    dentro de una tupla '''


class JSParser(Parser):
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
    error_id = [0, 0]
    tokens = JSLexer.tokens

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
        'param': 17,
        'callValue': 18,
        'returnVoid': 19,
        'returnValue': 20,
        'alertEnt': 21,
        'alertCad': 22,
        'inputEnt': 23,
        'inputCad': 24
    }

    def __init__(self, lista_reglas_, TS_, declaration_scope_, declarando_funcion_, global_shift_):
        self.lista_reglas = lista_reglas_
        self.TS = TS_
        self.declaration_scope = declaration_scope_
        self.declarando_funcion = declarando_funcion_
        self.global_shift = global_shift_
        self.num_temp = 0
        self.num_etiq = 0
        self.TS.new_table()
        self.shift = 0
        self.declaration_scope[0] = False
        self.function_scope = False
        self.return_type = None
        self.pos_id_fun = None
        self.number_function = 0
        self.ci = None
        self.initialize_global = []

    def initialize(self, p_ID):
        if p_ID[2]:
            self.initialize_global.append(p_ID[:2])

    # TODO: COMENTAR NUEVOS MÉTODOS AÑADIDOS
    def parse(self, tokens):
        super().parse(tokens)

        if self.initialize_global:
            init = [self.gen(oper='=',op1=0,res=i)[0] for i in self.initialize_global]
            self.ci = self.gen(oper='comment',res='\n; Inicializacion variables globales') + init +\
                      self.gen(oper='comment',res='; Fin de inicializacion variables globales\n') + self.ci

        self.print_ci(self.ci,'CI-Memoria.txt',self.format_tuple_memoria) 
        
        self.convert_ci(self.ci)
        self.print_ci(self.ci,'CI-Output.txt',self.format_tuple_gco)
        
    @_('D')
    def B(self, p):
        self.lista_reglas.append(1)

        d_cod = p.D[-1][1]
        b_cod = d_cod

        self.ci = b_cod
        return

    @_('F D')
    def D(self, p):
        self.lista_reglas.append(2)

        f_cod = p.F[-1][1]
        d1_cod = p.D[-1][1]
        d_cod = f_cod + d1_cod
        return (None, d_cod, [None]),

    @_('G D')
    def D(self, p):
        self.lista_reglas.append(3)

        g_cod = p.G[-1][1]
        d_cod = g_cod + p.D[-1][1]
        return (None, d_cod, [None]),

    @_('')
    def D(self, p):
        self.lista_reglas.append(4)

        d_cod = [None]
        return (None, d_cod, [None]),

    @_('IF ABPAREN E CEPAREN S')
    def G(self, p):
        if p.E[0] != self.LOG_TYPE:
            self.semantic_error(1, p.lineno)

        self.lista_reglas.append(5)

        g_desp = self.nueva_etiq()
        e_lugar = p.E[-1][0]
        e_cod = p.E[-1][1]
        s_cod = p.S[-1][1]
        g_cod = self.gen(oper='comment', res='\n; ---- Inicio de if simple') + \
                self.gen(oper='comment', res='\n; Inicio de condicion') + e_cod + \
                self.gen(oper='comment', res='; Fin de condicion\n') + \
                self.gen(oper='if=goto', op1=e_lugar, op2=0, res=g_desp) + \
                self.gen(oper='comment', res='\n; Inicio de sentencia') + s_cod + \
                self.gen(oper='comment', res='; Fin de sentencia\n') + \
                self.gen(oper=':', op1=g_desp) + self.gen(oper='comment', res='; ---- Fin de if simple\n')
        return (None, g_cod, [None]),

    @_('S')
    def G(self, p):
        self.lista_reglas.append(6)
        s_cod = p.S[-1][1]
        g_cod = s_cod
        return (None, g_cod, [None]),

    @_('H PUNTOYCOMA')
    def S(self, p):
        self.lista_reglas.append(7)
        g_cod = p.H[-1][1]
        h_cod = g_cod
        return (None, h_cod, [None]),

    @_('ID ABPAREN I CEPAREN')
    def H(self, p):

        return_value = self.TS.get_attribute(p.ID[0], p.ID[1], self.ATTR_RETURN_VALUE)

        i_cod_e = p.I[-1][1]
        i_cod_p = p.I[-1][2]
        etiq = self.TS.get_attribute(p.ID[0], p.ID[1], self.ATTR_LABEL)

        # TODO: mirar any
        if any(cod is not None for cod in i_cod_e):
            i_cod_e = self.gen(oper='comment',
                           res='\n; Inicio de asignación de literales en temporales') + i_cod_e + \
                           self.gen(oper='comment', res='; Fin de asignación de literales en temporales\n')

        # for i in i_cod_e:
        #     if i is not None:
        #         i_cod_e = self.gen(oper='comment',
        #                            res='\n; Inicio de asignación de literales en temporales') + i_cod_e + \
        #                   self.gen(oper='comment', res='; Fin de asignación de literales en temporales\n')
        #         break

        for i in i_cod_p:
            if i is not None:
                i_cod_p = self.gen(oper='comment', res='\n; Inicio de paso de parámetros') + i_cod_p + \
                          self.gen(oper='comment', res='; Fin de paso de parámetros\n')
                break

        h_lugar = None
        h_cod = self.gen(oper='comment', res='\n; ---- Inicio de llamada a funcion') + i_cod_e + i_cod_p

        if return_value != self.VOID_TYPE:
            h_lugar = self.nueva_temp(return_value)
            h_cod = h_cod + self.gen(res=h_lugar, oper='CallValue', op1=etiq) + \
                    self.gen(oper='comment', res='; ---- Fin de llamada a funcion\n')
        else:
            h_cod = h_cod + self.gen(res=h_lugar, oper='CallVoid', op1=etiq) + \
                    self.gen(oper='comment', res='; ---- Fin de llamada a funcion\n')
        if self.TS.get_attribute(p.ID[0], p.ID[1], self.ATTR_TYPE) != self.FUNCTION_TYPE:
            self.error_id = p.ID
            self.semantic_error(15, p.lineno)
        elif self.TS.get_attribute(p.ID[0], p.ID[1], self.ATTR_NUM_PARAMS) == 0 and p.I[0] == self.VOID_TYPE:
            return self.TS.get_attribute(p.ID[0], p.ID[1], self.ATTR_RETURN_VALUE), (None, h_cod, [None])
        elif self.TS.get_attribute(p.ID[0], p.ID[1], self.ATTR_NUM_PARAMS) != len(p.I[0]):
            self.error_id = p.ID
            self.semantic_error(2, p.lineno)

        for expected_type, found_type in zip(self.TS.get_attribute(p.ID[0], p.ID[1], self.ATTR_TYPE_PARAMS), p.I[0]):
            if expected_type != found_type:
                self.error_id = p.ID
                self.semantic_error(3, p.lineno)

        self.lista_reglas.append(8)

        self.initialize(p.ID)
        return return_value, (h_lugar, h_cod, [None])

    @_('E J')
    def I(self, p):
        list = p.J[0]
        list.insert(0, p.E[0])

        self.lista_reglas.append(9)

        i_cod_p = self.gen(oper='param', op1=p.E[-1][0]) + p.J[-1][2]
        i_cod_e = p.E[-1][1] + p.J[-1][1]

        return list, (None, i_cod_e, i_cod_p)

    @_('COMA E J')
    def J(self, p):
        list = p.J[0]
        list.insert(0, p.E[0])

        self.lista_reglas.append(10)

        j_cod_p = self.gen(oper='param', op1=p.E[-1][0]) + p.J[-1][2]
        j_cod_e = p.E[-1][1] + p.J[-1][1]

        return list, (None, j_cod_e, j_cod_p)

    @_('')
    def J(self, p):
        self.lista_reglas.append(11)

        j_cod_p = [None]
        j_cod_e = [None]

        return [], (None, j_cod_e, j_cod_p)

    @_('')
    def I(self, p):
        self.lista_reglas.append(12)

        i_cod_p = [None]
        i_cod_e = [None]

        return self.VOID_TYPE, (None, i_cod_e, i_cod_p)

    @_('K PUNTOYCOMA')
    def S(self, p):
        self.lista_reglas.append(13)
        k_cod = p.K[-1][1]
        s_cod = k_cod
        return (None, s_cod, [None]),

    @_('ID OPASIG E')
    def K(self, p):
        if self.TS.get_attribute(p.ID[0], p.ID[1], self.ATTR_TYPE) != p.E[0]:
            self.error_id = p.ID
            self.semantic_error(10, p.lineno)

        self.lista_reglas.append(14)

        self.initialize(p.ID)
        e_cod = p.E[-1][1]
        e_lugar = p.E[-1][0]
        k_cod = self.gen(oper='comment', res='\n; Inicio de asignación') + \
                e_cod + self.gen(oper='=', res=(p.ID[0], p.ID[1]), op1=e_lugar) + \
                self.gen(oper='comment', res='; Fin de asignación\n')
        return (None, k_cod, [None]),

    @_('ALERT ABPAREN E CEPAREN PUNTOYCOMA')
    def S(self, p):
        if p.E[0] != self.STRING_TYPE and p.E[0] != self.INT_TYPE:
            self.semantic_error(4, p.lineno)

        self.lista_reglas.append(15)

        e_cod = p.E[-1][1]
        s_cod = self.gen(oper='comment', res='\n; Inicio de llamada a alert') + \
                e_cod + self.gen(oper='alert', op1=p.E[-1][0]) + \
                self.gen(oper='comment', res='; Fin de llamada a alert\n')

        return (None, s_cod, [None]),

    @_('INPUT ABPAREN ID CEPAREN PUNTOYCOMA')
    def S(self, p):
        type = self.TS.get_attribute(p.ID[0], p.ID[1], self.ATTR_TYPE)
        if type != self.STRING_TYPE and type != self.INT_TYPE:
            self.error_id = p.ID
            self.semantic_error(5, p.lineno)

        self.lista_reglas.append(16)

        self.initialize(p.ID)
        s_cod = self.gen(oper='comment', res='\n; Inicio de llamada a input') + \
                self.gen(oper='input', res=(p.ID[0], p.ID[1])) + \
                self.gen(oper='comment', res='; Fin de llamada a input\n')

        return (None, s_cod, [None]),

    @_('RETURN L PUNTOYCOMA')
    def S(self, p):
        if not self.function_scope:
            self.semantic_error(7, p.lineno)
        if p.L[0] != self.return_type:
            self.semantic_error(9, p.lineno)

        self.lista_reglas.append(17)

        l_cod = p.L[-1][1]
        if l_cod is not None:
            l_lugar = p.L[-1][0]
            s_cod = l_cod + self.gen(oper='returnValue', op1=l_lugar)
        else:
            s_cod = self.gen(oper='returnVoid')
        return (None, s_cod, [None]),

    @_('E')
    def L(self, p):
        self.lista_reglas.append(18)

        e_cod = p.E[-1][1]
        e_lugar = p.E[-1][0]

        l_cod = e_cod
        l_lugar = e_lugar

        return p.E[0], (l_lugar, l_cod, [None])

    @_('')
    def L(self, p):
        self.lista_reglas.append(19)

        l_cod = [None]

        return self.VOID_TYPE, (None, l_cod, [None])

    # Hasta aquí Alex

    @_('LET M T ID PUNTOYCOMA')
    def G(self, p):
        if not self.function_scope:
            self.shift = self.global_shift[0]
        self.TS.add_attribute(p.ID[0], p.ID[1], self.ATTR_TYPE, p.T[0][0])
        self.TS.add_attribute(p.ID[0], p.ID[1], self.ATTR_DESP, self.shift)
        self.shift += p.T[0][1]
        if not self.function_scope:
            self.global_shift[0] = self.shift
        self.declaration_scope[0] = False

        self.lista_reglas.append(20)

        self.initialize(p.ID)
        if p.T[0][0] == self.STRING_TYPE:
            g_cod = self.gen(oper='=', res=(p.ID[0], p.ID[1]), op1='""')
        else:
            g_cod = self.gen(oper='=', res=(p.ID[0], p.ID[1]), op1=0)
        return (None, g_cod, [None]),

    @_('')
    def M(self, p):
        self.declaration_scope[0] = True
        self.lista_reglas.append(21)
        return

    @_('NUMBER')
    def T(self, p):
        self.lista_reglas.append(22)
        return (self.INT_TYPE, 1),

    @_('BOOLEAN')
    def T(self, p):
        self.lista_reglas.append(23)
        return (self.LOG_TYPE, 1),

    @_('STRING')
    def T(self, p):
        self.lista_reglas.append(24)
        return (self.STRING_TYPE, 64),

    @_('FOR ABPAREN N PUNTOYCOMA E PUNTOYCOMA O CEPAREN ABLLAVE C CELLAVE')
    def G(self, p):
        if p.E[0] != self.LOG_TYPE:
            self.semantic_error(6, p.lineno)

        self.lista_reglas.append(25)

        g_inicio = self.nueva_etiq()
        g_desp = self.nueva_etiq()
        n_cod = p.N[-1][1]
        e_lugar = p.E[-1][0]
        e_cod = p.E[-1][1]
        o_cod = p.O[-1][1]
        c_cod = p.C[-1][1]
        g_cod = self.gen(oper='comment', res='\n; ---- Inicio de for') + \
                self.gen(oper='comment', res='\n;  Inicio de inicializacion') + n_cod + \
                self.gen(oper='comment', res=';  Fin de inicializacion\n') + self.gen(oper=':', op1=g_inicio) + \
                self.gen(oper='comment', res='\n;  Inicio de condicion') + e_cod + \
                self.gen(oper='comment', res=';  Fin de condicion\n') + \
                self.gen(oper='if=goto', op1=e_lugar, op2=0, res=g_desp) + \
                self.gen(oper='comment', res='\n;  Inicio del cuerpo') + c_cod + \
                self.gen(oper='comment', res=';  Fin del cuerpo\n') + \
                self.gen(oper='comment', res='\n;  Inicio de actualización ') + o_cod + \
                self.gen(oper='comment', res=';  Fin de actualizacion\n') + \
                self.gen(oper='goto', res=g_inicio) + self.gen(oper=':', op1=g_desp) + \
                self.gen(oper='comment', res='; ---- Fin de for\n')
        return (None, g_cod, [None]),

    @_('K')
    def N(self, p):
        self.lista_reglas.append(26)

        n_cod = p.K[-1][1]
        return (None, n_cod, [None]),

    @_('')
    def N(self, p):
        self.lista_reglas.append(27)

        n_cod = [None]
        return (None, n_cod, [None]),

    @_('K')
    def O(self, p):
        self.lista_reglas.append(28)

        o_cod = p.K[-1][1]
        return (None, o_cod, [None]),

    @_('OPESP ID')
    def O(self, p):
        if self.TS.get_attribute(p.ID[0], p.ID[1], self.ATTR_TYPE) != self.INT_TYPE:
            self.error_id = p.ID
            self.semantic_error(11, p.lineno)

        self.lista_reglas.append(29)

        self.initialize(p.ID)
        id_lugar = (p.ID[0], p.ID[1])
        o_cod = self.gen(oper='comment', res='\n; Inicio de --id sin asignacion') \
                + self.gen(res=id_lugar, oper='=-', op1=id_lugar, op2=1) \
                + self.gen(oper='comment', res='; Fin de --id sin asignacion\n')
        return (None, o_cod, [None]),

    @_('')
    def O(self, p):
        self.lista_reglas.append(30)

        o_cod = [None]
        return (None, o_cod, [None]),

    @_('G C')
    def C(self, p):
        self.lista_reglas.append(31)

        g_cod = p.G[-1][1]
        c1_cod = p.C[-1][1]
        c_cod = g_cod + c1_cod
        return (None, c_cod, [None]),

    @_('')
    def C(self, p):
        self.lista_reglas.append(32)

        c_cod = [None]
        return (None, c_cod, [None]),

    @_('F1 F2 F3')
    def F(self, p):
        self.TS.destroy_table(len(self.TS.tables) - 1)
        self.function_scope = False
        self.return_type = None
        self.shift = self.global_shift[0]

        self.lista_reglas.append(33)

        f1_cod = p.F1[-1][1]
        f2_cod = p.F2[-1][1]
        f3_cod = p.F3[-1][1]
        f_cod = self.gen(oper='comment', res='\n; -------- Inicio de funcion') + \
                f1_cod + f2_cod + f3_cod + self.gen(oper='comment', res='') + \
                self.gen(oper='returnVoid') + self.gen(oper='comment', res='; -------- Fin de funcion\n')
        return (None, f_cod, [None]),

    @_('FUNCTION P Q ID')
    def F1(self, p):
        self.TS.new_table()
        self.global_shift[0] = self.shift
        self.shift = 0
        self.pos_id_fun = p.ID
        self.function_scope = True

        self.TS.add_attribute(p.ID[0], p.ID[1], self.ATTR_TYPE, self.FUNCTION_TYPE)
        if p.Q[0] == 'void':
            self.return_type = p.Q[0]
            self.TS.add_attribute(p.ID[0], p.ID[1], self.ATTR_RETURN_VALUE, self.VOID_TYPE)
        else:
            self.return_type = p.Q[0]
            self.TS.add_attribute(p.ID[0], p.ID[1], self.ATTR_RETURN_VALUE, p.Q[0])
        self.TS.add_attribute(p.ID[0], p.ID[1], self.ATTR_LABEL,
                              '#EtiqFun' + str(self.number_function))

        self.lista_reglas.append(34)

        self.initialize(p.ID)
        etiq_fun = self.TS.get_attribute(p.ID[0], p.ID[1], self.ATTR_LABEL)
        f1_cod = self.gen(oper=':', op1=etiq_fun)
        return (None, f1_cod, [None]),

    @_('')
    def P(self, p):
        self.lista_reglas.append(35)
        return

    @_('T')
    def Q(self, p):
        self.declaration_scope[0] = True

        self.lista_reglas.append(36)
        return p.T[0][0],

    @_('')
    def Q(self, p):
        self.declaration_scope[0] = True

        self.lista_reglas.append(37)
        return self.VOID_TYPE,

    @_('ABPAREN A CEPAREN')
    def F2(self, p):
        list = p.A[0]
        if list == self.VOID_TYPE:
            self.TS.add_attribute(self.pos_id_fun[0], self.pos_id_fun[1], self.ATTR_NUM_PARAMS, 0)
            self.TS.add_attribute(self.pos_id_fun[0], self.pos_id_fun[1], self.ATTR_TYPE_PARAMS, self.VOID_TYPE)
        else:
            types = []
            for i in range(0, len(list), 2):
                type = list[i]
                pos = list[i + 1]
                self.TS.add_attribute(pos[0], pos[1], self.ATTR_TYPE, type[0])
                self.TS.add_attribute(pos[0], pos[1], self.ATTR_DESP, self.shift)
                self.shift += type[1]
                types.append(type[0])
            self.TS.add_attribute(self.pos_id_fun[0], self.pos_id_fun[1], self.ATTR_NUM_PARAMS, len(types))
            self.TS.add_attribute(self.pos_id_fun[0], self.pos_id_fun[1], self.ATTR_TYPE_PARAMS, types)

        self.number_function += 1
        self.declaration_scope[0] = False
        self.declarando_funcion[0] = False

        self.lista_reglas.append(38)

        f2_cod = [None]
        return (None, f2_cod, [None]),

    @_('T ID W')
    def A(self, p):
        list = p.W[0]
        list.insert(0, p.ID)
        list.insert(0, p.T[0])

        self.lista_reglas.append(39)

        self.initialize(p.ID)
        return list,

    @_('')
    def A(self, p):
        self.lista_reglas.append(40)
        return self.VOID_TYPE,

    @_('COMA T ID W')
    def W(self, p):
        list = p.W[0]
        list.insert(0, p.ID)
        list.insert(0, p.T[0])

        self.lista_reglas.append(41)

        self.initialize(p.ID)
        return list,

    @_('')
    def W(self, p):
        self.lista_reglas.append(42)
        return [],

    @_('ABLLAVE C CELLAVE')
    def F3(self, p):
        self.lista_reglas.append(43)

        f3_cod = p.C[-1][1]
        return (None, f3_cod, [None]),

    @_('E OPLOG R')
    def E(self, p):
        if p.E[0] != self.LOG_TYPE or p.R[0] != self.LOG_TYPE:
            self.semantic_error(12, p.lineno)

        self.lista_reglas.append(44)

        e_lugar = self.nueva_temp(self.LOG_TYPE)
        e1_lugar = p.E[-1][0]
        e1_cod = p.E[-1][1]
        r_lugar = p.R[-1][0]
        r_cod = p.R[-1][1]
        e_cod = self.gen(oper='comment', res='\n; Inicio de conjuncion logica') + e1_cod + r_cod + \
                self.gen(res=e_lugar, oper='=and', op1=e1_lugar, op2=r_lugar) + \
                self.gen(oper='comment', res='; Fin de conjuncion logica\n')
        return self.LOG_TYPE, (e_lugar, e_cod, [None])

    @_('R')
    def E(self, p):
        self.lista_reglas.append(45)

        e_lugar = p.R[-1][0]
        e_cod = p.R[-1][1]
        return p.R[0], (e_lugar, e_cod, [None])

    @_('R OPREL U')
    def R(self, p):
        if p.R[0] != self.INT_TYPE or p.U[0] != self.INT_TYPE:
            self.semantic_error(13, p.lineno)

        self.lista_reglas.append(46)

        r_true = self.nueva_etiq()
        r_despues = self.nueva_etiq()
        r1_lugar = p.R[-1][0]
        r1_cod = p.R[-1][1]
        u_lugar = p.U[-1][0]
        u_cod = p.U[-1][1]
        r_lugar = self.nueva_temp(self.INT_TYPE)
        r_cod = self.gen(oper='comment', res='\n; Inicio de operador de igualdad') + r1_cod + u_cod + self.gen(
            oper='if=goto', op1=r1_lugar, op2=u_lugar, res=r_true) + \
                self.gen(res=r_lugar, oper='=', op1=0) + self.gen(oper='goto', res=r_despues) + \
                self.gen(oper=':', op1=r_true) + self.gen(res=r_lugar, oper='=', op1=1) + \
                self.gen(oper=':', op1=r_despues) + self.gen(oper='comment', res='; Inicio de operador de igualdad\n')
        return self.LOG_TYPE, (r_lugar, r_cod, [None])

    @_('U')
    def R(self, p):
        self.lista_reglas.append(47)

        r_lugar = p.U[-1][0]
        r_cod = p.U[-1][1]
        return p.U[0], (r_lugar, r_cod, [None])

    @_('U OPARIT V')
    def U(self, p):
        if p.U[0] != self.INT_TYPE or p.V[0] != self.INT_TYPE:
            self.semantic_error(14, p.lineno)

        self.lista_reglas.append(48)

        u_lugar = self.nueva_temp(self.INT_TYPE)
        u1_lugar = p.U[-1][0]
        u1_cod = p.U[-1][1]
        v_lugar = p.V[-1][0]
        v_cod = p.V[-1][1]
        u_cod = self.gen(oper='comment', res='\n; Inicio de resta aritmetica') + u1_cod + \
                v_cod + self.gen(res=u_lugar, oper='=-', op1=u1_lugar, op2=v_lugar) + \
                self.gen(oper='comment', res='; Fin de resta aritmetica\n')
        return self.INT_TYPE, (u_lugar, u_cod, [None])

    @_('V')
    def U(self, p):
        self.lista_reglas.append(49)

        u_lugar = p.V[-1][0]
        u_cod = p.V[-1][1]
        return p.V[0], (u_lugar, u_cod, [None])

    @_('OPESP ID')
    def V(self, p):
        if self.TS.get_attribute(p.ID[0], p.ID[1], self.ATTR_TYPE) != self.INT_TYPE:
            self.error_id = p.ID
            self.semantic_error(11, p.lineno)

        self.lista_reglas.append(50)

        self.initialize(p.ID)
        v_lugar = self.nueva_temp(self.INT_TYPE)
        id_lugar = (p.ID[0], p.ID[1])
        v_cod = self.gen(oper='comment', res='\n; Inicio de --id con asignacion') + \
                self.gen(res=id_lugar, oper='=-', op1=id_lugar, op2=1) + \
                self.gen(res=v_lugar, oper='=', op1=id_lugar) + \
                self.gen(oper='comment', res='; Fin de --id con asignacion\n')
        return self.INT_TYPE, (v_lugar, v_cod, [None])

    @_('ID')
    def V(self, p):
        self.lista_reglas.append(51)

        self.initialize(p.ID)
        v_lugar = (p.ID[0], p.ID[1])
        v_cod = [None]
        return self.TS.get_attribute(p.ID[0], p.ID[1], self.ATTR_TYPE), (v_lugar, v_cod, [None])

    @_('ABPAREN E CEPAREN')
    def V(self, p):
        self.lista_reglas.append(52)

        v_lugar = p.E[-1][0]
        v_cod = p.E[-1][1]
        return p.E[0], (v_lugar, v_cod, [None])

    @_('H')
    def V(self, p):
        self.lista_reglas.append(53)

        v_lugar = p.H[-1][0]
        v_cod = p.H[-1][1]
        return p.H[0], (v_lugar, v_cod, [None])

    @_('CTEENTERA')
    def V(self, p):
        self.lista_reglas.append(54)

        v_lugar = self.nueva_temp(self.INT_TYPE)
        v_cod = self.gen(res=v_lugar, oper='=', op1=p.CTEENTERA)
        return self.INT_TYPE, (v_lugar, v_cod, [None])

    @_('CADENA')
    def V(self, p):
        self.lista_reglas.append(55)

        v_lugar = self.nueva_temp(self.STRING_TYPE)
        v_cod = self.gen(res=v_lugar, oper='=', op1=p.CADENA)
        return self.STRING_TYPE, (v_lugar, v_cod, [None])

    @_('CTELOGICA')
    def V(self, p):
        self.lista_reglas.append(56)

        v_lugar = self.nueva_temp(self.LOG_TYPE)
        v_cod = self.gen(res=v_lugar, oper='=', op1=p.CTELOGICA)
        return self.LOG_TYPE, (v_lugar, v_cod, [None])

    # -----------------------Variables and labels management functions-----------------------
    def nueva_temp(self, type):
        res = f'~Temp{self.num_temp}'
        self.num_temp += 1
        id_ = self.TS.add_entry(res)
        self.TS.add_attribute(id_[0], id_[1], self.ATTR_DESP, self.shift)
        self.TS.add_attribute(id_[0], id_[1], self.ATTR_TYPE, type)

        self.shift += 64 if type == self.STRING_TYPE else 1
        if not self.function_scope:
            self.global_shift[0] = self.shift
        return id_

    def nueva_etiq(self):
        res = f'#Etiq{self.num_etiq}'
        self.num_etiq += 1
        return res

    def gen(self, oper, op1=None, op2=None, res=None):

        oper_ = oper
        op1_ = op1
        op2_ = op2
        res_ = res

        match oper:
             case '=':
                 if type(op1) is tuple:
                     if self.TS.get_attribute(op1[0], op1[1], self.ATTR_TYPE) == self.STRING_TYPE:
                         oper_ = '=Cad'
                     else:
                         oper_ = '=EL'
                 else:
                     if type(op1) is int:
                         op1_ = ('ent', op1)
                         oper_ = '=EL'
                     else:
                         op1_= ('cad', op1)
                         oper_ = '=Cad'
             case 'if=goto' | '=-':
                 if type(op2) is not tuple:
                     if type(op2) is int:
                         op2_ = ('ent', op2)
                     else:
                         op2_ = ('cad', op2)
             case 'comment':
                 return [(f'{res_}',)]
             case 'input':
                 if self.TS.get_attribute(res[0], res[1], self.ATTR_TYPE) == self.STRING_TYPE:
                     oper_ = 'inputCad'
                 else:
                     oper_ = 'inputEnt'
             case 'alert':
                 if self.TS.get_attribute(op1[0], op1[1], self.ATTR_TYPE) == self.STRING_TYPE:
                     oper_ = 'alertCad'
                 else:
                     oper_ = 'alertEnt'

        return [(oper_, op1_, op2_, res_)]

    def convert_ci(self, ci):
        list = []
        for tuple_ in ci:
            if tuple_ is not None:
                list.append(self.convert_tuple(tuple_))
        self.ci = list

    def convert_tuple(self, tuple_):
        if len(tuple_) == 1 and type(tuple_[0]) is str: return tuple_# Comment
        oper = self.OPERATOR_CODE[tuple_[0]]
        cod_3d = [oper]
        for elem in tuple_[1:]:
            if elem is not None:
                match type(elem):
                    case builtins.str:  # ('#Etiq2')
                        cod = self.OPERAND_CODE['etiq']
                        elem = (cod, elem)
                    case builtins.tuple:
                        if type(elem[0]) == int: # (0,1) corresponde a variable
                            cod = self.scope_code(elem)
                            desp = self.TS.get_attribute(elem[0], elem[1], self.ATTR_DESP)
                            elem = (cod, desp)
                        elif type(elem[0]) == str:  # ('ent',2) | ('cad',"hola")
                            cod = self.OPERAND_CODE[elem[0]]
                            elem = (cod, elem[1])

                        # match type(elem[0]):  # match anidado innecesario
                        #     case type_ if type_ == int: # (0,1) corresponde a variable
                        #         cod = self.scope_code(elem)
                        #         desp = self.TS.get_attribute(elem[0], elem[1], self.ATTR_DESP)
                        #         elem = (cod, desp)
                        #     case type_ if type_ == str:    # ('ent',2) | ('cad',"hola")
                        #         cod = self.OPERAND_CODE[elem[0]]
                        #         elem = (cod, elem[1])

            cod_3d.append(elem)
        return tuple(cod_3d)

    def scope_code(self, var):
        if self.TS.is_global(var):
            return 1
        else:
            return 2

    def print_ci(self, cod, out, format_function): # TODO: refactorizar cod por ci
         with open(out, 'w') as out_fd:
            res = self.format_ci(cod,format_function)
            print(res, file=out_fd)

    def format_ci(self, cod, format_function):
        res = ''
        for tuple_ in cod:
            if tuple_ is not None:
                if len(tuple_) == 1 and type(tuple_[0]) is str:  # Comments
                    res += f'{tuple_[0]}\n'
                else:
                    res += format_function(tuple_)
        return res

    def format_tuple_memoria(self, tuple_):
        res = '['
        for elem in tuple_:
            if elem is None:
                pass
            elif type(elem) is tuple and type(elem[0]) is int:
                res += self.TS.get_lex_entry(elem[0], elem[1])[self.ATTR_LEXEM]
            elif type(elem) is tuple:
                res += str(elem[1])
            else:
                res += str(elem)
            res += ', '
        return f'{res[:-2]}]\n'

    def format_tuple_gco(self, tuple_):  # oper -> cod | tupla_var -> (global/local,desp)
        res = '['
        for elem in tuple_:
            if elem is not None:
                if type(elem) is tuple:
                    res += f"({', '.join([str(i) for i in elem])})"
                else:
                    res += f'{elem}'
            res += ', '
        return f'{res[:-2]}]\n'

    # -----------------------Error management functions-----------------------

    def perror(self, *args, **kwargs):
        """The C perror function equivalent in python.

        Args:
            args(Direct Pointer): the arguments to be print
            kwargs(Indirect Pointer): the configuration applied to those arguments
        """
        print(*args, file=sys.stderr, **kwargs)

    def error(self, p):
        """Handles syntax errors

        This function will output through standard error the syntax error detected
        showing the user some hints to solve the problem

        Args:
             p(Token): The syntactic rule where the problem was located
         """
        res = 'Error en la sintaxis:\n\t '
        if not p:
            res += 'Expresión incompleta, se esperaban más elementos'
            self.perror(res)
            exit(2)
        else:
            res += f'Elemento no esperado "{p.type.lower()}" en la linea {p.lineno}'
            self.perror(res)
            exit(3)

    def semantic_error(self, error_code, lineno):
        """Handles semantic errors

        This function will output through standard error
        the semantic error detected showing the user some hints to solve the problem

        Args:
            error_code(int): The error code of issue
            lineno(int): The line where the error occurred
        """
        self.perror(f'Error en la linea {lineno}:\n\t{self.get_error_code(error_code)}')
        exit(4)

    def get_error_code(self, error_code):
        """semantic_error auxiliary function

        Returns the error line indicated by the error_code parameter.
        It will also update to the last error_id provided.

        Args:
            error_code(int): The error code of issue
        """
        params = self.TS.get_attribute(self.error_id[0], self.error_id[1], self.ATTR_TYPE_PARAMS)
        if params is None:
            params = []
        error_code_dict = {
            1: f'La condición debe ser un lógico',
            2: f'El número de parámetros introducidos no son los esperados, deberían ser "{len(params)}"',
            3: f'El tipo de los parámetros no es el esperado, se esperaban "{params}"',
            4: f'La expresión introducida no es una cadena o un entero',
            5: f'La variable introducida no es de tipo cadena o entero',
            6: f'La condición debe ser un lógico',
            7: f'No puede haber una sentencia return fuera de una función',
            8: f'No se permite la definición de funciones anidadas',
            9: f'El tipo de retorno no corresponde con el tipo de retorno de la función, se esperaba "{self.return_type}"',
            10: f'El tipo de la variable a asignar no corresponde con el tipo asignado',
            11: f'El operador especial "--" solo trabaja con tipos de datos enteros',
            12: f'El operador lógico "&&" solo trabaja con tipos de datos lógicos',
            13: f'El operador de relación "==" solo trabaja con tipos de datos enteros',
            14: f'El operador aritmético "-" solo trabaja con tipos de datos enteros',
            15: f'La variable no se puede invocar como una función'
        }
        return error_code_dict.get(error_code)
