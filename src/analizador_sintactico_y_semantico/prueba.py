#gen(string del operador, lugar/valor/etiq, lugar/valor, lugar/etiq)
#.lugar=(id_table, id_pos)

self.gen(oper='if=', op1=e_lugar, op2=('ent', 0), res=('etiq', g_desp))
self.gen(oper=':', op1=('etiq', g_desp))
self.gen(oper='=', res=(p.ID[0], p.ID[1]), op1=e_lugar)
self.gen(res=v_lugar, oper='=', op1=p.CTEENTERA)


# #Param
# gen(param, buscaLugarTS(id.pos))
# gen(param, E.lugar)                             gen(oper='param', oper1=E.lugar)
#
# #CallValue
# gen(H.lugar, =, call, buscaEtiquetaTS(id.pos))  gen(res=H.lugar, oper='callValue', oper1=etiq(id.pos))
#
# #Alert
# gen(alert)                                      gen(oper='alert')
#
# #Input
# gen(input)                                      gen(oper='input')
#
# #ReturnVoid
# gen(return)                                     gen(oper='return')
#
# #ReturnValue
# gen(return, L.lugar)                            gen(oper='return', res=L.lugar)
#
# #: etiqueta
# gen(:, G.inicio)                                self.gen(oper=':', op1=('etiq', g_desp))
#
# #goto etiqueta
# gen(goto, G.inicio)                             gen(oper='goto',oper1='etiqueta')


#=EL y =CAD
gen(buscaLugarTS(id.pos), =, E.lugar)           gen(res=v_lugar, oper='=', op1=E.lugar) # preguntar TS tipo

self.gen(res=v_lugar, oper='=', op1=p.CTEENTERA) # preguntar tipo con type('sdad'), return op1=('ent',p.CTEENTERA)

# gen(E.lugar, =, E1.lugar, AND, R.lugar)         gen(res=e.lugar, oper1='e1.lugar',oper='=AND', oper2='r.lugar')

gen(if, E.lugar, =, 0, goto, G.desp)              gen(oper='if=', op1=e_lugar, op2=('ent', 0), res=('etiq', g_desp))
gen(if, R1.lugar, =, U.lugar, goto, G.desp)     # lo mismo que antes  pero con op2 (línea 37)

gen(U.lugar, =, U1.lugar, -, V.lugar)             gen(oper1=u1_lugar,oper='=-', oper2='lugar',res='lugar')
gen(id.lugar, =, id.lugar, -, 1)                  gen(oper1=id_lugar,oper='=-', oper2=('ent',0),res='lugar') #lo mismo que antes  pero con op2 (línea 41)


match oper:
    case '=':
        if type(op1)==cad:

        else:


    case 'if=' | '=-':

    case _:
