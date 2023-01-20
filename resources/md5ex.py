
class MD5Ex:

    hex = [ '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f' ]

    def bshift( self, val1, val2, dir = 'r', zero_fill = False ):

        if dir == 'l':
            return val1 << val2

        if dir == 'r' and zero_fill == True:
            return (val1 % 0x100000000) >> val2

        return val1 >> val2

    def charCodeAt( self, str, pos ):
        return ord( str[pos] )

    def hash( self, n ):
        return self.binHex( self.binHash( self.strBin(n), len(n) << 3))

    def hashUTF8( self, n ):
        return self.hash(self.encUTF8(n))

    def hashRaw( self, n ):
        return self.binStr(self.binHash(self.strBin(n), len(n) << 3))

    def hashRawUTF8( self, n ):
        return self.hashRaw(self.encUTF8(n))

    def hashStretch( self, n, h, i ):
        return self.binHex(self.binHashStretch(n, h, i))

    def binHashStretch( self, n, h, i ):

        e = self.encUTF8(n)
        g = h + e
        o = 32 + len(e) << 3
        a = self.strBin(e)
        u = len(a)

        g = self.binHash(self.strBin(g), len(g) << 3)
        if not i:
            i = 1024
        r = 0

        while r < i:
            g = self.binHexBin(g)
            t = 0
            while t < u:
                g[8 + t] = a[t]
                t = t + 1
            g = self.binHash(g, o)
            r = r + 1

        return g

    def encUTF8( self, n ):

        r = ''
        t = 0
        f = len(n) - 1

        while t <= f:

            h = self.charCodeAt(n, t)
            t+=1
            i = self.charCodeAt(n, t)

            if t < f and 55296 <= h and h <= 56319 and 56320 <= i and i <= 57343:
                h = 65536 + self.bshift((1023 & h), 10, 'l') + (1023 & i)
                t+=1

            if h <= 127:
                r += char(h)
            else:
                if h <= 2047:
                    #r += char(192 | h >>> 6 & 31, 128 | 63 & h)
                    True
                else:
                    if h <= 65535:
                        #r += char(224 | h >>> 12 & 15, 128 | h >>> 6 & 63, 128 | 63 & h)
                        True
                    #else:
                        #h <= 2097151 and (r += char(240 | h >>> 18 & 7, 128 | h >>> 12 & 63, 128 | h >>> 6 & 63, 128 | 63 & h))

        return r

    def strBin( self, n ):

        i = self.bshift( len(n), 3, 'l' )
        r = {}
        h = 0

        while h < i:
            tmp = self.bshift( h, 5 )
            r[tmp] = r.get(tmp, 0) | self.bshift( (255 & self.charCodeAt( n, self.bshift( h, 3 ))), (31 & h), 'l' )
            h += 8

        return r

    def binHex( self, n ):

        r = 0
        t = self.bshift( len(n), 5, 'l' )
        i = 0

        while i < t:
            h = self.bshift( n.get( self.bshift( r, 5 ), 0 ), (31 & r), 'r', True ) & 255
            i = self.bshift( h, 4, 'r', True ) & 15
            h &= 15
            t += int(self.hex[i] + self.hex[h], 16)
            r += 8

        return t

    def binStr( self, n ):

        r = ''
        t = self.bshift( len(n), 5, 'l' )
        i = 0

        while i < t:
            h = self.bshift( n.get( self.bshift( i, 5 ), 0 ), (31 & i), 'r', True ) & 255
            r += char(h)
            i += 8

        return r

    def binHexBin( self, n ):

        t = self.bshift( len(n), 5, 'l' )
        f = []
        r = 0

        while r < t:

            h = self.bshift( n.get( self.bshift( r, 5 ), 0 ), (31 & r), 'r', True ) & 255
            i = self.bshift( h, 4, 'r', True ) & 15
            h &= 15

            tmp2 = 48
            if 9 < i:
                tmp2 = 87

            tmp3 = 48
            if 9 < h:
                tmp3 = 87

            tmp = self.bshift( r, 4 )
            f[tmp] = f[tmp] | tmp2 + i + self.bshift( self.bshift( (tmp3 + h), 8, 'l'), self.bshift((15 & r), 1, 'l'), 'l' )
            r += 8

        return f

    def fff( self, n, h, i, r, t, f, e, g ):

        o = (65535 & n) + (65535 & g) + (65535 & t) + (65535 & e)
        g = self.bshift( self.bshift( n, 16 ) + self.bshift( g, 16, 'r') + self.bshift( t, 16 ) + self.bshift( e, 16 ) + self.bshift( o, 16 ), 16, 'l' )
        g = g | 65535 & o
        g = self.bshift( g, f, 'l' ) | self.bshift( g, ( 32 - f ), 'r', True )
        o = (65535 & g) + (65535 & h)
        g = self.bshift( self.bshift( g, 16 ) + self.bshift( h, 16 ) + self.bshift( o, 16 ), 16, 'l' )

        return g | 65535 & o

    def ff( self, n, h, i, r, t, f, e ):

        g = h & i | ~h & r
        return self.fff(n, h, i, r, t, f, e, g)

    def gg( self, n, h, i, r, t, f, e ):

        g = h & r | i & ~r
        return self.fff(n, h, i, r, t, f, e, g)

    def hh( self, n, h, i, r, t, f, e ):

        g = h ^ i ^ r
        return self.fff(n, h, i, r, t, f, e, g)

    def ii( self, n, h, i, r, t, f, e ):

        g = i ^ (h | ~r)
        return self.fff(n, h, i, r, t, f, e, g)

    def binHash( self, n, h ):

        a = 1732584193
        u = -271733879
        s = -1732584194
        c = 271733878

        tmp = self.bshift( h, 5 )
        n[ tmp ] = n.get( tmp, 0 ) | self.bshift( 128, (31 & h), 'l' )
        tmp = 14 + self.bshift( ( h + 64 ), self.bshift( 9, 4, 'l' ), 'r', True )
        n[ tmp ] = h
        i = len(n)
        r = 0

        while r < i:

            t = a
            f = u
            e = s
            g = c

            a = self.ff(a, u, s, c, n.get((r + 0), 0), 7, -680876936)
            c = self.ff(c, a, u, s, n.get((r + 1), 0), 12, -389564586)
            s = self.ff(s, c, a, u, n.get((r + 2), 0), 17, 606105819)
            u = self.ff(u, s, c, a, n.get((r + 3), 0), 22, -1044525330)
            a = self.ff(a, u, s, c, n.get((r + 4), 0), 7, -176418897)
            c = self.ff(c, a, u, s, n.get((r + 5), 0), 12, 1200080426)
            s = self.ff(s, c, a, u, n.get((r + 6), 0), 17, -1473231341)
            u = self.ff(u, s, c, a, n.get((r + 7), 0), 22, -45705983)
            a = self.ff(a, u, s, c, n.get((r + 8), 0), 7, 1770035416)
            c = self.ff(c, a, u, s, n.get((r + 9), 0), 12, -1958414417)
            s = self.ff(s, c, a, u, n.get((r + 10), 0), 17, -42063)
            u = self.ff(u, s, c, a, n.get((r + 11), 0), 22, -1990404162)
            a = self.ff(a, u, s, c, n.get((r + 12), 0), 7, 1804603682)
            c = self.ff(c, a, u, s, n.get((r + 13), 0), 12, -40341101)
            s = self.ff(s, c, a, u, n.get((r + 14), 0), 17, -1502002290)
            u = self.ff(u, s, c, a, n.get((r + 15), 0), 22, 1236535329)
            a = self.gg(a, u, s, c, n.get((r + 1), 0), 5, -165796510)
            c = self.gg(c, a, u, s, n.get((r + 6), 0), 9, -1069501632)
            s = self.gg(s, c, a, u, n.get((r + 11), 0), 14, 643717713)
            u = self.gg(u, s, c, a, n.get((r + 0), 0), 20, -373897302)
            a = self.gg(a, u, s, c, n.get((r + 5), 0), 5, -701558691)
            c = self.gg(c, a, u, s, n.get((r + 10), 0), 9, 38016083)
            s = self.gg(s, c, a, u, n.get((r + 15), 0), 14, -660478335)
            u = self.gg(u, s, c, a, n.get((r + 4), 0), 20, -405537848)
            a = self.gg(a, u, s, c, n.get((r + 9), 0), 5, 568446438)
            c = self.gg(c, a, u, s, n.get((r + 14), 0), 9, -1019803690)
            s = self.gg(s, c, a, u, n.get((r + 3), 0), 14, -187363961)
            u = self.gg(u, s, c, a, n.get((r + 8), 0), 20, 1163531501)
            a = self.gg(a, u, s, c, n.get((r + 13), 0), 5, -1444681467)
            c = self.gg(c, a, u, s, n.get((r + 2), 0), 9, -51403784)
            s = self.gg(s, c, a, u, n.get((r + 7), 0), 14, 1735328473)
            u = self.gg(u, s, c, a, n.get((r + 12), 0), 20, -1926607734)
            a = self.hh(a, u, s, c, n.get((r + 5), 0), 4, -378558)
            c = self.hh(c, a, u, s, n.get((r + 8), 0), 11, -2022574463)
            s = self.hh(s, c, a, u, n.get((r + 11), 0), 16, 1839030562)
            u = self.hh(u, s, c, a, n.get((r + 14), 0), 23, -35309556)
            a = self.hh(a, u, s, c, n.get((r + 1), 0), 4, -1530992060)
            c = self.hh(c, a, u, s, n.get((r + 4), 0), 11, 1272893353)
            s = self.hh(s, c, a, u, n.get((r + 7), 0), 16, -155497632)
            u = self.hh(u, s, c, a, n.get((r + 10), 0), 23, -1094730640)
            a = self.hh(a, u, s, c, n.get((r + 13), 0), 4, 681279174)
            c = self.hh(c, a, u, s, n.get((r + 0), 0), 11, -358537222)
            s = self.hh(s, c, a, u, n.get((r + 3), 0), 16, -722521979)
            u = self.hh(u, s, c, a, n.get((r + 6), 0), 23, 76029189)
            a = self.hh(a, u, s, c, n.get((r + 9), 0), 4, -640364487)
            c = self.hh(c, a, u, s, n.get((r + 12), 0), 11, -421815835)
            s = self.hh(s, c, a, u, n.get((r + 15), 0), 16, 530742520)
            u = self.hh(u, s, c, a, n.get((r + 2), 0), 23, -995338651)
            a = self.ii(a, u, s, c, n.get((r + 0), 0), 6, -198630844)
            c = self.ii(c, a, u, s, n.get((r + 7), 0), 10, 1126891415)
            s = self.ii(s, c, a, u, n.get((r + 14), 0), 15, -1416354905)
            u = self.ii(u, s, c, a, n.get((r + 5), 0), 21, -57434055)
            a = self.ii(a, u, s, c, n.get((r + 12), 0), 6, 1700485571)
            c = self.ii(c, a, u, s, n.get((r + 3), 0), 10, -1894986606)
            s = self.ii(s, c, a, u, n.get((r + 10), 0), 15, -1051523)
            u = self.ii(u, s, c, a, n.get((r + 1), 0), 21, -2054922799)
            a = self.ii(a, u, s, c, n.get((r + 8), 0), 6, 1873313359)
            c = self.ii(c, a, u, s, n.get((r + 15), 0), 10, -30611744)
            s = self.ii(s, c, a, u, n.get((r + 6), 0), 15, -1560198380)
            u = self.ii(u, s, c, a, n.get((r + 13), 0), 21, 1309151649)
            a = self.ii(a, u, s, c, n.get((r + 4), 0), 6, -145523070)
            c = self.ii(c, a, u, s, n.get((r + 11), 0), 10, -1120210379)
            s = self.ii(s, c, a, u, n.get((r + 2), 0), 15, 718787259)
            u = self.ii(u, s, c, a, n.get((r + 9), 0), 21, -343485551)

            o = (65535 & a) + (65535 & t)
            a = self.bshift( ( self.bshift( a, 16 ) + self.bshift( t, 16 ) + self.bshift( o, 16 ) ), 16, 'l' ) | 65535 & o
            o = (65535 & u) + (65535 & f)
            u = self.bshift( ( self.bshift( u, 16 ) + self.bshift( f, 16 ) + self.bshift( o, 16 ) ), 16, 'l' ) | 65535 & o
            o = (65535 & s) + (65535 & e)
            s = self.bshift( ( self.bshift( s, 16 ) + self.bshift( e, 16 ) + self.bshift( o, 16 ) ), 16, 'l' ) | 65535 & o
            o = (65535 & c) + (65535 & g)
            c = self.bshift( ( self.bshift( c, 16 ) + self.bshift( g, 16 ) + self.bshift( o, 16 ) ), 16, 'l' ) | 65535 & o

            r = r + 16

        return {0:a, 1:u, 2:s, 3:c}
