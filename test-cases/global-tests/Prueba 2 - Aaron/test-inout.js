let number numero;
let string cadena;
function string pide_cadena(){
    let string c;
    alert("Introduce la cadena:\n");
    input(c);
    return c;
}
function number pide_numero(){
    let number n;
    alert("Introduce el numero:\n");
    input(n);
    return n;
}
cadena = pide_cadena();
alert("La cadena leida fue:\n");
alert(cadena);
alert("\n");
numero = pide_numero();
alert("El numero leido fue:\n");
alert(numero);