import Levenshtein as lv
import re
from common import SHIFT_KEY, CAPS_KEY

KEYBOARD_TYPE = 'US'
layout_matrix = {
    "US": ([
        "`1234567890-=",
        "~!@#$%^&*()_+",
        " qwertyuiop[]\\",
        " QWERTYUIOP{}|",
        " asdfghjkl;'\n",
        " ASDFGHJKL:\"\n",
        " zxcvbnm,./",
        " ZXCVBNM<>?",
        "         ",
        "         "
    ], 2),
    "MOBILE_ANDROID": ([
        "qwertyuiop",
        "QWERTYUIOP",
        "1234567890",
        "~`|......",
        "asdfghjkl",
        "ASDFGHJKL",
        "@#$%&-+()",
        "....^.={}",
        "zxcvbnm",
        "ZXCVBNM",
        "*\"':;!?",
        "\....[]",
        "/      .",
        ",_    /.",
        ",<    >.",
        ",<    >."], 4)
}


class Keyboard(object):
    _keyboard_type = 'US'
    # some random parameters, need to learn later
    _shift_discount = 0.8

    def __init__(self, _type, shift_discount=0.8):
        self._keyboard_type = _type
        self._keyboard, self._num_shift = layout_matrix[self._keyboard_type]
        self._shift_discount = shift_discount
        self._loc_map = {}
        assert len(self._keyboard) % self._num_shift==0, "Problem in Keyboard layout. "\
            "Expecting the size of the keyboard ({}) to be multiple of num_shift ({})."\
            .format(len(self._keyboard), self._num_shift)

    def char2key(self, char, capslock_state):
        assert self._keyboard_type == 'US', "Not yet supported non-US keyboards"
        r, c, shift = self.loc(self, char)
        if capslock_state == 1 and char.isalpha():   # caps lock is on
            shift = (shift+1) % 2  # No need to press shift
        return shift, self._keyboard[r*self._num_shift][c]

    def remove_shift(self, char):
        r, c, shift = self.loc(char)
        if shift:
            char = self.loc2char(r*self._num_shift, c)
        return char, shift

    def add_shift(self, char):
        r, c, shift = self.loc(char)
        if not shift:
            char = self.loc2char(r*self._num_shift+1, c)
        return char, shift
        
    def change_shift(self, char):
        if not char.isalpha(): return char
        r, c, shift = self.loc(char)
        nshift = (shift+1) % self._num_shift
        char = self.loc2char(r*self._num_shift + nshift, c)
        return char, shift
        
    def loc(self, char):
        """
        return location of a key, the row, column and shift on
        or off.
        """
        KM, num_shift = self._keyboard, self._num_shift
        if not self._loc_map:
            self._loc_map = {ch: (i/num_shift, j, i % num_shift)
                             for i, r in enumerate(KM)
                             for j, ch in enumerate(r)}
            self._loc_map[' '] = (3, 0, 0)
        if char not in self._loc_map:
            raise Exception( "Could not find location of: <{}>".format(repr(char)))
            
        return self._loc_map.get(char, (-1, -1, -1))

    def loc2char(self, r, c):
        """
        Given loc (r,c) returns the actual character
        """
        if r>=0 and r<len(self._keyboard):
            if c>=0 and c<len(self._keyboard[r]):
                return self._keyboard[r][c]
        return ''

    def num_shift(self):
        return self._num_shift

    def keyboard_dist(self, key_o, key_t):
        """
        Returns how close the keys are in keyboard
        key_o = original key
        key_w = typed key
        (Though the output is order agnostic :P)
        """
        oi, oj, oshift = self.loc(key_o)
        ti, tj, tshift = self.loc(key_t)
        print key_o, oi, oj, oshift, '>>><<<<',
        print ti, tj, tshift, key_t

        return abs(oi-ti) + abs(oj-tj) + \
            self._shift_discount*abs(oshift-tshift)

    def is_keyboard_prox(self, s, d):
        """
        Checks whether two words are close in terms of keys
        :param s: character
        :param d: character
        :return: weight
        """
        d = self.keyboard_dist(s, d)
        return d < 1.0
    
    def keyboard_prox_chars(self, char):
        """Returns the closed by characters of character @c in standard US
        Keyboard.
        :param c: character
        :return: a list of characters
        """
        i, j, shift = self.loc(char)
        ret = []
        KM, num_shift = self._keyboard, self._num_shift
        for sh in xrange(num_shift):
            for r in range(i-1, i+2):
                for c in range(j-1, j+2):
                    ch = self.loc2char(r*num_shift+sh, c)
                    if ch and ch != ' ' and ch != char:
                        ret.append(ch)
        return ret

    def keyboard_prox_key(self, char):
        """Returns the closed by characters of character @c in standard US
        Keyboard.
        :param c: character
        :return: a list of keys
        """
        if char == SHIFT_KEY: 
            return [CAPS_KEY]
        elif char == CAPS_KEY:
            return [SHIFT_KEY]

        i, j, shift = self.loc(char)
        ret = []
        KM, num_shift = self._keyboard, self._num_shift
        for r in range(i-1, i+2):
            for c in range(j-1, j+2):
                ch = self.loc2char(r*num_shift, c)
                if ch and ch != ' ':
                    ret.append(ch)
        return ret

    def word_to_key_presses(self, word):
        """
        Converts a @word into a key press sequence for the keyboard KB.
        >>> KB = Keyboard('US')
        >>> KB.word_to_key_presses('Password12!@')
        <s>password12<s>1<s>2
        >>> KB.word_to_key_presses('PASSword!@')
        <c>pass</c>word<s>1<s>2
        >>> KB.word_to_key_presses('PAasWOrd') # this is not what it should but close!
        <s>p<s>aas<s>w<s>ord
        <c>pa</c>as<c>wo</c>rd
        """
        caps_key = CAPS_KEY
        shift_key = SHIFT_KEY
        assert KEYBOARD_TYPE == 'US', "Not implemented for mobile"
        new_str = ''
        # Add shift keys
        for i, ch in enumerate(word):
            try:
                ch, shift = self.remove_shift(ch)
            except Exception, e:
                print e,  repr(word)
                raise e
            if shift:
                new_str += shift_key + ch
            else:
                new_str += ch

        # finding continuous use of shift and replace that with capslock
        for s in re.findall(r'(({0}[a-z]){{3,}})'.format(shift_key), new_str):
            o_s, _ = s
            n_s = re.sub(r'{0}([a-z])'.format(shift_key), r'\1'.format(caps_key), o_s)
            new_str = re.sub(re.escape(o_s), '{0}{1}{0}'.format(caps_key, n_s), new_str)

        
        # drop <c>a<c> to <s>a
        new_str = re.sub(r'{0}(.){0}'.format(re.escape(caps_key)),
                         r'{}\1'.format(shift_key),
                         new_str)  

        # move the last capslock to the end
        # PASSOWRD123 -> <c>password<c>123 -> <c>password123<c>
        new_str = re.sub(r'{0}([^a-z]+)$'.format(re.escape(caps_key)),
                         r'\1{0}'.format(caps_key),
                         new_str)  
        
        # convert last sequence of shift into caps sequence
        # passwoRD123 -> passwo<s>r<s>d123 -> passwo<c>rd123<c>
        # r'(<s>[a-z][^a-z]*)+{2,}$ ->
        m = re.match(r'.*?(?P<endshifts>({0}[a-z][^a-z{0}]*){{2,}}({0}.[^a-z]*)*)$'.format(shift_key), new_str)
        if m:
            s = m.group('endshifts')
            ns = caps_key + re.sub(r'{0}([a-z])'.format(shift_key), r'\1', s) + caps_key
            # print m.groups(), ns, s
            new_str = new_str.replace(s, ns)

        return new_str

    def print_key_press(self, keyseq):
        """print the @key_str as the human readable format.
        """
        return keyseq.replace(SHIFT_KEY, '<s>').replace(CAPS_KEY, '<c>')
        
    def key_presses_to_word(self, keysq):
        """This is the same function as word_to_key_presses, just trying to
        make it more efficient. Remeber the capslock and convert the
        shift.

        """
        caps_key = CAPS_KEY
        shift_key = SHIFT_KEY
        assert KEYBOARD_TYPE == 'US', "Not implemented for mobile"
        ret = ''
        i = 0
        caps = 0
        shift = 0
        while i<len(keysq):
            a = keysq[i]
            if keysq[i] == caps_key:
                caps = (caps+1) % self._num_shift
            elif keysq[i] == shift_key:
                shift = 1
            else:
                if a.isalpha():
                    a = self.add_shift(a)[0] if caps^shift == 1 else a
                else:
                    a = self.add_shift(a)[0] if shift else a
                shift = 0
                ret += a
            i += 1
        return ret


    def key_presses_to_word_slow(self, keyseq):
        """
        Converts a keypress sequence to a word
        """
        caps_key = CAPS_KEY
        shift_key = SHIFT_KEY
        assert KEYBOARD_TYPE == 'US', "Not implemented for mobile"

        word = keyseq
        def caps_change(m):
            return ''.join(self.change_shift(c)[0] if c !=shift_key else shift_key
                           for c in m.group(1))

        def shift_change(m):
            return ''.join(self.add_shift(c)[0] if c != caps_key else caps_key
                           for c in m.group(1))

        word = re.sub(r'({0})+'.format(shift_key), r'\1', word)
        word = re.sub(r'({0})+'.format(caps_key), r'\1', word)
        # only swap <s><c> to <c><s>
        word = re.sub(r'({1}{0})+([a-zA-Z])'.format(caps_key, shift_key),
                      r'{0}{1}\2'.format(caps_key, shift_key), 
                      word)

        if word.count(caps_key)%2 == 1:
            word += caps_key

        try:
            # apply all shift keys
            word = re.sub(r'{0}+([\w\W])'.format(shift_key),
                          shift_change, word)
            # apply all capslocks
            word = re.sub(r'{0}(.*?){0}'.format(caps_key),
                          caps_change, word)
        except Exception, e:
            print ">>>> I could not figure this out: {!r}, stuck at {!r}".format(keyseq, word)
            raise e
        word = word.strip(shift_key).strip(caps_key)
        return word


def find_typo_type(word_o, word_t):
    """
    Find the type of the typo by considering bunch of strategies.
      1. match the original string from the back of the typo string and see if
         final output of the typo was correct or not. This tells that there was
         a typo in the beginning which was fixed later
      2. After 1 we shall get
    :param word_o: original string
    :param word_t: typed string
    :return: What type of typo it is
    """

    pass



if __name__ == '__main__':
    kb = Keyboard('US')
    ks = '{s}wo{c}rd123{s}{c}'.format(c=CAPS_KEY, s=SHIFT_KEY)
    # p1 = kb.word_to_key_presses(pw1)
    # print "{!r} -> {!r} --> {!r}".format(pw1, p1, pw11)
    print "{!r} -> {!r}".format(ks, kb.key_presses_to_word(ks))
