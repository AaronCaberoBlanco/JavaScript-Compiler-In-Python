let number x;
x = 1;

function print_x(){
    alert(x);
    alert("\n");

    x = x - 1;
    if(x == 0)
        print_x();
}

print_x();
