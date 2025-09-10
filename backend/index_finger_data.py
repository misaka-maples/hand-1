import numpy as np
import math

def crank_angle(L):
    return 0.080942*L**3-1.152077*L**2+20.112629*L-9.926147
def index_inger_swing_angle(L):
    return -0.00070197*L**3 + 0.02521*L**2 - 2.271*L + 21.1282
if __name__ == "__main__":
    print(index_inger_swing_angle(10.5))