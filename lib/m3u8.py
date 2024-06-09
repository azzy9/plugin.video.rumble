"""
Class to handle M3U8 files created by Azzy9
"""

class m3u8:

    def process( self, m3u8_data ):

        """ method to process the m3u8 files """

        urls = []
        try:
            m3u8_data = m3u8_data.rstrip().split('\n')
            if m3u8_data:
                # don't need first 2 lines
                m3u8_data.pop(0)
                m3u8_data.pop(0)

                line_amount = 0
                resolution = ''
                for line in m3u8_data:

                    if line_amount % 2 == 0:
                        resolution = line.split('x')
                        resolution = resolution[-1]
                    else:
                        urls.append(( resolution, line ))

                    line_amount +=1

                urls = urls[::-1]

        except Exception:
            pass

        return urls
