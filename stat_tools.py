
import math
from random import gauss

def MakeCallable(callable, param):
    def subroutine(x):
        return callable(x, param)
    return subroutine

def GetMeanValue(seq):
    return sum(seq) / len(seq)

def SigmaSubroutine(xi, mean):
    return (xi - mean) ** 2

def GetSigma(seq):
    m = get_mean_value(seq)
    sub_sum = make_callable(sigma_subroutine, m)
    mp = map(sub_sum, seq)
    summary, n = 0, 0
    for i in mp:
        n += 1
        summary += i
    return math.sqrt(summary / n)

def GeneratePositiveIntegerGauss(m, s, n):
    val = -1
    while not 0 <= val <= n:
        val = round(gauss(m,s))
    return int(val)
