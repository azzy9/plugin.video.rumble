
class MD5Ex:

    hex = [ '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f' ]

    def bshift( self, val1, val2, dir = 'r', zero_fill = False ):

        if dir == 'l':
            return val1 << val2

        if dir == 'r' and zero_fill == True:
            return (val1 % 0x100000000) >> val2

        return val1 >> val2

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

        #while t <= f:
            #h = n.charCodeAt(t++)
            #t < f && 55296 <= h && h <= 56319 && 56320 <= (i = n.charCodeAt(t)) && i <= 57343 && (h = 65536 + ((1023 & h) << 10) + (1023 & i), t++)
            #h <= 127 ? r += String.fromCharCode(h) : h <= 2047 ? r += String.fromCharCode(192 | h >>> 6 & 31, 128 | 63 & h) : h <= 65535 ? r += String.fromCharCode(224 | h >>> 12 & 15, 128 | h >>> 6 & 63, 128 | 63 & h) : h <= 2097151 && (r += String.fromCharCode(240 | h >>> 18 & 7, 128 | h >>> 12 & 63, 128 | h >>> 6 & 63, 128 | 63 & h))
        return r

    def strBin( self, n ):

        i = self.bshift( len(n), 3, 'l' )
        r = []
        h = 0

        while h < i:
            tmp = self.bshift( h, 5, 'r' )
            r[tmp] = r[tmp] | self.bshift( (255 & n.charCodeAt( self.bshift( h, 3, 'r' ))), (31 & h), 'l' )
            h += 8

        return r

    def binHex( self, n ):

        r = ''
        t = self.bshift( len(n), 5, 'l' )
        i = 0

        while i < t:
            h = self.bshift( n[ self.bshift( r, 5, 'r' ) ], (31 & r), 'r', True ) & 255
            i = self.bshift( h, 4, 'r', True ) & 15
            h &= 15
            t += self.hex[i] + self.hex[h]
            r += 8

        return t

    def binStr( self, n ):

        r = ''
        t = self.bshift( len(n), 5, 'l' )
        i = 0

        while i < t:
            h = self.bshift( n[ self.bshift( i, 5, 'r' ) ], (31 & i), 'r', True ) & 255
            r += String.fromCharCode(h)
            i += 8

        return r

    def binHexBin( self, n ):

        t = self.bshift( len(n), 5, 'l' )
        f = []
        r = 0

        while r < t:

            h = self.bshift( n[ self.bshift( r, 5, 'r' ) ], (31 & r), 'r', True ) & 255
            i = self.bshift( h, 4, 'r', True ) & 15
            h &= 15

            tmp2 = 48
            if 9 < i:
                tmp2 = 87

            tmp3 = 48
            if 9 < h:
                tmp3 = 87

            tmp = self.bshift( r, 4, 'r' )
            f[tmp] = f[tmp] | tmp2 + i + self.bshift( self.bshift( (tmp3 + h), 8, 'l'), self.bshift((15 & r), 1, 'l'), 'l' )
            r += 8

        return f

    def fff( self, n, h, i, r, t, f, e, g ):

        o = (65535 & n) + (65535 & g) + (65535 & t) + (65535 & e);
        g = self.bshift( self.bshift( n, 16, 'r' ) + self.bshift( g, 16, 'r') + self.bshift( t, 16, 'r' ) + self.bshift( e, 16, 'r' ) + self.bshift( o, 16, 'r' ), 16, 'l' );
        g = g | 65535 & o;
        g = self.bshift( g, f, 'l' ) | self.bshift( g, ( 32 - f ), 'r', true ) ;
        o = (65535 & g) + (65535 & h)
        g = self.bshift( self.bshift( g, 16, 'r' ) + self.bshift( h, 16, 'r' ) + self.bshift( o, 16, 'r' ), 16, 'l' );

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

        tmp = self.bshift( h, 5, 'r' )
        n[ tmp ] = n[ tmp ] | self.bshift( 128, (31 & h), 'l' )
        tmp = 14 + self.bshift( ( h + 64 ), self.bshift( 9, 4, 'l' ), 'r', True )
        n[ tmp ] = h
        i = len(n)
        r = 0

        while r < i:

            t = a
            f = u
            e = s
            g = c

            a = self.ff(a, u, s, c, n[r + 0], 7, -680876936)
            c = self.ff(c, a, u, s, n[r + 1], 12, -389564586)
            s = self.ff(s, c, a, u, n[r + 2], 17, 606105819)
            u = self.ff(u, s, c, a, n[r + 3], 22, -1044525330)
            a = self.ff(a, u, s, c, n[r + 4], 7, -176418897)
            c = self.ff(c, a, u, s, n[r + 5], 12, 1200080426)
            s = self.ff(s, c, a, u, n[r + 6], 17, -1473231341)
            u = self.ff(u, s, c, a, n[r + 7], 22, -45705983)
            a = self.ff(a, u, s, c, n[r + 8], 7, 1770035416)
            c = self.ff(c, a, u, s, n[r + 9], 12, -1958414417)
            s = self.ff(s, c, a, u, n[r + 10], 17, -42063)
            u = self.ff(u, s, c, a, n[r + 11], 22, -1990404162)
            a = self.ff(a, u, s, c, n[r + 12], 7, 1804603682)
            c = self.ff(c, a, u, s, n[r + 13], 12, -40341101)
            s = self.ff(s, c, a, u, n[r + 14], 17, -1502002290)
            u = self.ff(u, s, c, a, n[r + 15], 22, 1236535329)
            a = self.gg(a, u, s, c, n[r + 1], 5, -165796510)
            c = self.gg(c, a, u, s, n[r + 6], 9, -1069501632)
            s = self.gg(s, c, a, u, n[r + 11], 14, 643717713)
            u = self.gg(u, s, c, a, n[r + 0], 20, -373897302)
            a = self.gg(a, u, s, c, n[r + 5], 5, -701558691)
            c = self.gg(c, a, u, s, n[r + 10], 9, 38016083)
            s = self.gg(s, c, a, u, n[r + 15], 14, -660478335)
            u = self.gg(u, s, c, a, n[r + 4], 20, -405537848)
            a = self.gg(a, u, s, c, n[r + 9], 5, 568446438)
            c = self.gg(c, a, u, s, n[r + 14], 9, -1019803690)
            s = self.gg(s, c, a, u, n[r + 3], 14, -187363961)
            u = self.gg(u, s, c, a, n[r + 8], 20, 1163531501)
            a = self.gg(a, u, s, c, n[r + 13], 5, -1444681467)
            c = self.gg(c, a, u, s, n[r + 2], 9, -51403784)
            s = self.gg(s, c, a, u, n[r + 7], 14, 1735328473)
            u = self.gg(u, s, c, a, n[r + 12], 20, -1926607734)
            a = self.hh(a, u, s, c, n[r + 5], 4, -378558)
            c = self.hh(c, a, u, s, n[r + 8], 11, -2022574463)
            s = self.hh(s, c, a, u, n[r + 11], 16, 1839030562)
            u = self.hh(u, s, c, a, n[r + 14], 23, -35309556)
            a = self.hh(a, u, s, c, n[r + 1], 4, -1530992060)
            c = self.hh(c, a, u, s, n[r + 4], 11, 1272893353)
            s = self.hh(s, c, a, u, n[r + 7], 16, -155497632)
            u = self.hh(u, s, c, a, n[r + 10], 23, -1094730640)
            a = self.hh(a, u, s, c, n[r + 13], 4, 681279174)
            c = self.hh(c, a, u, s, n[r + 0], 11, -358537222)
            s = self.hh(s, c, a, u, n[r + 3], 16, -722521979)
            u = self.hh(u, s, c, a, n[r + 6], 23, 76029189)
            a = self.hh(a, u, s, c, n[r + 9], 4, -640364487)
            c = self.hh(c, a, u, s, n[r + 12], 11, -421815835)
            s = self.hh(s, c, a, u, n[r + 15], 16, 530742520)
            u = self.hh(u, s, c, a, n[r + 2], 23, -995338651)
            a = self.ii(a, u, s, c, n[r + 0], 6, -198630844)
            c = self.ii(c, a, u, s, n[r + 7], 10, 1126891415)
            s = self.ii(s, c, a, u, n[r + 14], 15, -1416354905)
            u = self.ii(u, s, c, a, n[r + 5], 21, -57434055)
            a = self.ii(a, u, s, c, n[r + 12], 6, 1700485571)
            c = self.ii(c, a, u, s, n[r + 3], 10, -1894986606)
            s = self.ii(s, c, a, u, n[r + 10], 15, -1051523)
            u = self.ii(u, s, c, a, n[r + 1], 21, -2054922799)
            a = self.ii(a, u, s, c, n[r + 8], 6, 1873313359)
            c = self.ii(c, a, u, s, n[r + 15], 10, -30611744)
            s = self.ii(s, c, a, u, n[r + 6], 15, -1560198380)
            u = self.ii(u, s, c, a, n[r + 13], 21, 1309151649)
            a = self.ii(a, u, s, c, n[r + 4], 6, -145523070)
            c = self.ii(c, a, u, s, n[r + 11], 10, -1120210379)
            s = self.ii(s, c, a, u, n[r + 2], 15, 718787259)
            u = self.ii(u, s, c, a, n[r + 9], 21, -343485551)

            o = (65535 & a) + (65535 & t)
            a = self.bshift( ( self.bshift( a, 16, 'r' ) + self.bshift( t, 16, 'r' ) + self.bshift( o, 16, 'r' ) ), 16, 'l' ) | 65535 & o
            o = (65535 & u) + (65535 & f)
            u = self.bshift( ( self.bshift( u, 16, 'r' ) + self.bshift( f, 16, 'r' ) + self.bshift( o, 16, 'r' ) ), 16, 'l' ) | 65535 & o
            o = (65535 & s) + (65535 & e)
            s = self.bshift( ( self.bshift( s, 16, 'r' ) + self.bshift( e, 16, 'r' ) + self.bshift( o, 16, 'r' ) ), 16, 'l' ) | 65535 & o
            o = (65535 & c) + (65535 & g)
            c = self.bshift( ( self.bshift( c, 16, 'r' ) + self.bshift( g, 16, 'r' ) + self.bshift( o, 16, 'r' ) ), 16, 'l' ) | 65535 & o

            r = r + 16

        return [a, u, s, c]
