function boolean f(number n, boolean b){
    b = true;
    return b;
}
function number h(string s){
    alert("Me ha llegado esta cadena: \n");
    alert(s);
    alert("\n");
    return 23-2;
}
function number dameNum(string s, boolean b){
    if(f(21,b))
        return h(s);
    return 0;
}
let string in;
alert("Introduce una cadena para transmitir a una funcion anidada \n");
input(in);
alert("Transmitiendo la cadena... \n");
dameNum(in,false);