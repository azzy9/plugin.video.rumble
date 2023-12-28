"""
MD5Ex class
Converted from JS to python by Azzy9
This is a class to generate hashes that is used by the Rumble platform to login
"""

class MD5Ex:

    """ MD5Ex class to create MD5 hashes """

    hex = [ '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f' ]

    def bit_shift( self, val1, val2, direction = 'r', zero_fill = False ):

        """ bit_shift method to allow zero filled bitshift which is not supported by python """

        if direction == 'l':
            return val1 << val2

        if direction == 'r' and zero_fill is True:
            return (val1 % 0x100000000) >> val2

        return val1 >> val2

    def char_code_at( self, str_in, pos ):

        """ essentially the ord method but with validation that is required """

        if pos < len( str_in ):
            return ord( str_in[pos] )

        return 0

    def hash( self, n ):

        """ hash method """

        return self.binHex( self.binHash( self.strBin(n), len(n) << 3))

    def hashUTF8( self, n ):

        """ hashUTF8 method """

        return self.hash(self.encUTF8(n))

    def hashRaw( self, n ):

        """ hashRaw method """

        return self.binStr(self.binHash(self.strBin(n), len(n) << 3))

    def hashRawUTF8( self, n ):

        """ hashRawUTF8 method """

        return self.hashRaw(self.encUTF8(n))

    def hashStretch( self, n, h, i ):

        """ hashStretch method """

        return self.binHex(self.binHashStretch(n, h, i))

    def binHashStretch( self, n, h, i ):

        """ binHashStretch method """

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
            r += 1

        return g

    def encUTF8( self, n ):

        """ encUTF8 method """

        # return string
        r_str = ''
        # character pos
        char_pos = 0
        # string length
        str_len = len(n) - 1

        while char_pos <= str_len:

            h = self.char_code_at(n, char_pos)
            char_pos += 1
            i = self.char_code_at(n, char_pos)

            if char_pos < str_len and 55296 <= h and h <= 56319 and 56320 <= i and i <= 57343:
                h = 65536 + self.bit_shift((1023 & h), 10, 'l') + (1023 & i)
                char_pos +=1

            if h <= 127:
                r_str += chr(h)
            else:
                if h <= 2047:
                    r_str += chr(192 | self.bit_shift( h, 6, 'r', True ) & 31, 128 | 63 & h)
                else:
                    if h <= 65535:
                        r_str += chr(224 | self.bit_shift( h, 12, 'r', True ) & 15, 128 | self.bit_shift( h, 6, 'r', True ) & 63, 128 | 63 & h)
                    else:
                        if h <= 2097151:
                            r_str += chr(240 | self.bit_shift( h, 18, 'r', True ) & 7, 128 | self.bit_shift( h, 12, 'r', True ) & 63, 128 | self.bit_shift( h, 6, 'r', True ) & 63, 128 | 63 & h)

        return r_str

    def strBin( self, n ):

        """ String to Binary """

        i = self.bit_shift( len(n), 3, 'l' )
        r = {}
        h = 0

        while h < i:
            tmp = self.bit_shift( h, 5 )
            r[tmp] = r.get(tmp, 0) | self.bit_shift( (255 & self.char_code_at( n, self.bit_shift( h, 3 ))), (31 & h), 'l' )
            h += 8

        return r

    def binHex( self, n ):

        """ Binary to Hex """

        t = ''
        f = self.bit_shift( len(n), 5, 'l' )
        r = 0

        while r < f:
            h = self.bit_shift( n.get( self.bit_shift( r, 5 ), 0 ), (31 & r), 'r', True ) & 255
            i = self.bit_shift( h, 4, 'r', True ) & 15
            h &= 15
            t += self.hex[i] + self.hex[h]
            r += 8

        return t

    def binStr( self, n ):

        """ Binary to String """

        r = ''
        t = self.bit_shift( len(n), 5, 'l' )
        i = 0

        while i < t:
            h = self.bit_shift( n.get( self.bit_shift( i, 5 ), 0 ), (31 & i), 'r', True ) & 255
            r += chr(h)
            i += 8

        return r

    def binHexBin( self, n ):

        """ binHexBin method """

        t = self.bit_shift( len(n), 5, 'l' )
        f = {}
        r = 0

        while r < t:

            h = self.bit_shift( n.get( self.bit_shift( r, 5 ), 0 ), (31 & r), 'r', True ) & 255
            i = self.bit_shift( h, 4, 'r', True ) & 15
            h &= 15

            tmp2 = 48
            if 9 < i:
                tmp2 = 87

            tmp3 = 48
            if 9 < h:
                tmp3 = 87

            tmp = self.bit_shift( r, 4 )
            f[tmp] = f.get(tmp, 0) | self.bit_shift( tmp2 + i + self.bit_shift( (tmp3 + h), 8, 'l'), self.bit_shift((15 & r), 1, 'l'), 'l' )
            r += 8

        return f

    def fghi( self, n, h, i, r, t, f, e, g ):

        """
        method that is used by ff,gg,hh,ii
        This was originally duplicated code in each method
        reduced code by creating a new method for it
        """

        o = (65535 & n) + (65535 & g) + (65535 & t) + (65535 & e)
        g = self.bit_shift( self.bit_shift( n, 16 ) + self.bit_shift( g, 16, 'r') + self.bit_shift( t, 16 ) + self.bit_shift( e, 16 ) + self.bit_shift( o, 16 ), 16, 'l' )
        g = g | 65535 & o
        g = self.bit_shift( g, f, 'l' ) | self.bit_shift( g, ( 32 - f ), 'r', True )
        o = (65535 & g) + (65535 & h)
        g = self.bit_shift( self.bit_shift( g, 16 ) + self.bit_shift( h, 16 ) + self.bit_shift( o, 16 ), 16, 'l' )

        return g | 65535 & o

    def ff( self, n, h, i, r, t, f, e ):

        """ ff method used in binHash """

        g = h & i | ~h & r
        return self.fghi(n, h, i, r, t, f, e, g)

    def gg( self, n, h, i, r, t, f, e ):

        """ gg method used in binHash """

        g = h & r | i & ~r
        return self.fghi(n, h, i, r, t, f, e, g)

    def hh( self, n, h, i, r, t, f, e ):

        """ hh method used in binHash """

        g = h ^ i ^ r
        return self.fghi(n, h, i, r, t, f, e, g)

    def ii( self, n, h, i, r, t, f, e ):

        """ ii method used in binHash """

        g = i ^ (h | ~r)
        return self.fghi(n, h, i, r, t, f, e, g)

    def binHash( self, n, h ):

        """ Binary to Hash """

        a = 1732584193
        u = -271733879
        s = -1732584194
        c = 271733878

        tmp = self.bit_shift( h, 5 )
        n[ tmp ] = n.get( tmp, 0 ) | self.bit_shift( 128, (31 & h), 'l' )
        tmp = 14 + self.bit_shift( self.bit_shift( ( h + 64 ), 9, 'r', True ), 4, 'l' )
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
            a = self.bit_shift( ( self.bit_shift( a, 16 ) + self.bit_shift( t, 16 ) + self.bit_shift( o, 16 ) ), 16, 'l' ) | 65535 & o
            o = (65535 & u) + (65535 & f)
            u = self.bit_shift( ( self.bit_shift( u, 16 ) + self.bit_shift( f, 16 ) + self.bit_shift( o, 16 ) ), 16, 'l' ) | 65535 & o
            o = (65535 & s) + (65535 & e)
            s = self.bit_shift( ( self.bit_shift( s, 16 ) + self.bit_shift( e, 16 ) + self.bit_shift( o, 16 ) ), 16, 'l' ) | 65535 & o
            o = (65535 & c) + (65535 & g)
            c = self.bit_shift( ( self.bit_shift( c, 16 ) + self.bit_shift( g, 16 ) + self.bit_shift( o, 16 ) ), 16, 'l' ) | 65535 & o

            r += 16

        return {0:a, 1:u, 2:s, 3:c}
