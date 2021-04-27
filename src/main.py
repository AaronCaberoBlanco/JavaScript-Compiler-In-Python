import sys
import os

'''Necessary imports to use the PDL-Procesator'''
from analizador_lexico.js_lexer import JSLexer
from analizador_sintactico_y_semantico.js_parser import JSParser
from tabla_simbolos.sym_table import SymTable
from src.generador_codigo_objeto.gco import GCO

'''Output files where we can see the different results of our input'''
tokens_file_ = 'Tokens.txt'
parse_file_ = 'Parse.txt'
TS_file_ = 'TS-Output.txt'
CO_file_ = 'CO-Output.ens'
# sys.stderr = open("Error.txt", "w")

'''The input where we obtain the program to analize'''
with open('Input.txt', 'r') as f:
    data = f.read()

'''Global variables to share between the lexer and the parser'''
symbol_table = SymTable()
declaration_scope = [False]
declarando_funcion = [False]
global_shift = [0]

'''Instantiation of both modules'''
with open(tokens_file_, 'w') as tokens_file:
    lexer = JSLexer(symbol_table, declaration_scope, tokens_file, declarando_funcion, global_shift)

    rule_list = []
    parser = JSParser(rule_list, symbol_table, declaration_scope, declarando_funcion, global_shift)
    parser.parse(lexer.get_token(data))

with open(parse_file_, 'w') as parse_file, open(TS_file_, "w") as TS_file:
    print(f"Ascendente {str(rule_list).strip('[]').replace(',', '')}", file=parse_file)
    symbol_table.write_table(TS_file)

with open(CO_file_, 'w') as CO_file:
    gco = GCO(CO_file, parser.ci, parser.size_RAs, symbol_table)
    gco.print_co(gco.convert_co())

# os.system('cd /home/dani/opt/ENS2001-Windows2 ; wine /home/dani/opt/ENS2001-Windows/winens.exe')

execute_simulator_cmd = 'wine /home/dani/opt/ENS2001-Windows/winens.exe'
# os.system(execute_simulator_cmd)
