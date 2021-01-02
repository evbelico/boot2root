from turtle import *
​
LETTER_WIDTH=125
START_X=0
LETTER_POS=(-50,0)
LETTER_RIGHT=(0, 180, 185, 0, 180, 0)
Y_OFFSET=(0, 0, 0, 0, 100, 0)
LETTER_IDX=0
​
def add_letter():
    up()
    if heading() > 270:
        right(heading()-270)
    else:
        left(270-heading())
    global LETTER_POS
    global LETTER_IDX
    setpos(*LETTER_POS)
    sety(Y_OFFSET[LETTER_IDX])
    right(LETTER_RIGHT[LETTER_IDX])
    LETTER_POS=(LETTER_POS[0] + LETTER_WIDTH, 0)
    down()
    LETTER_IDX += 1
​
def resolve_turtle(lst):
    for item in lst:
        item = item.rstrip()
        if not item:
            add_letter()
            continue
        elems = item.split()
        action = elems[0]
​
        if action == 'Avance':
            n = int(elems[1])
            forward(n)
        elif action == 'Recule':
            n = int(elems[1])
            backward(n)
        elif action == 'Tourne':
            n = int(elems[3])
            if elems[1] == 'droite':
                right(n)
            else:
                left(n)
        else:
            print(item)
​
​
if __name__ == '__main__':
    import sys
    setx(START_X)
​
    color('red', 'white')
    begin_fill()
    add_letter()
​
    with open(sys.argv[-1]) as toto:
        resolve_turtle(toto.readlines())
​
    end_fill()
    while(True):
        continue
