let number numero;
let string s;
numero = 5;
s = "hola\n";
function number f(number n, string saludo){
    let boolean seguir;
    seguir = true;
    for(global = 0; seguir; --n){
        alert(saludo);
        alert(n);
        alert("\n");
        if (n == 0)
            seguir = false;
    }
    return n;
}
alert("El ultimo valor de numero deberia ser -1\n");
numero = f(numero,s);
alert("El ultimo valor de numero es:\n");
alert(numero);
