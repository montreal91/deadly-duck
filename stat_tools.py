
import math
from random import gauss, random

def MakeCallable( callble, param ):
    def subroutine( x ):
        return callble( x, param )
    return subroutine

def GetMeanValue( seq ):
    return sum( seq ) / len( seq )

def SigmaSubroutine( xi, mean ):
    return ( xi - mean ) ** 2

def GetSigma( seq ):
    m = GetMeanValue( seq )
    sub_sum = MakeCallable( SigmaSubroutine, m )
    mp = map( sub_sum, seq )
    summary, n = 0, 0
    for i in mp:
        n += 1
        summary += i
    return math.sqrt( summary / n )

def GeneratePositiveIntegerGauss( m, s, n ):
    val = -1
    while not 1 <= val <= n:
        val = round( gauss( m, s ) )
    return int( val )

def LoadedToss( probability ):
    return random() < probability
