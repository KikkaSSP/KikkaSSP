
import logging

class SakuraScript():
    def __init__(self, script=''):
        self.tokens = []
        self.question_record = {}
        self.last_talk_exiting_surface = {}

        try:
            self.unserialize(script)
        except Exception:
            logging.error("ERROR SakuraScript: %s" % script)
            raise

    def is_digit(self, uchar):
        """判断一个unicode是否是数字"""
        return uchar >= u'\u0030' and uchar <= u'\u0039'

    def are_digits(self, string):
        p = 0
        if string[p] == '-':
            p += 1
        if string[p] == '\0':
            return False
        while string[p] != '\0':
            if not self.is_digit(string[p]):
                return False
            p += 1
        return True

    def is_alpha(self, uchar):
        """判断一个unicode是否是英文字母"""
        return (uchar >= u'\u0041' and uchar <= u'\u005a') or (uchar >= u'\u0061' and uchar <= u'\u007a')

    def serialize(self):
        script = ''
        for i in self.tokens:
            script += i[0] + i[1]
        return script

    def unserialize(self, script):
        if script == '':
            return

        vec = []
        acum = ''
        content = False
        is_first_question = True
        last_speaker = 0

        p = 0
        while p < len(script):
            c = script[p]
            p += 1

            if c == '\\' or c == '%':
                if script[p] == '\\' or script[p] == '%':
                    acum += c + script[p]
                    p += 1
                    continue

                start = p
                while p < len(script) \
                        and (self.is_alpha(script[p]) or
                             self.is_digit(script[p]) or
                             script[p] in ['!', '*', '&', '?', '_']):
                    p += 1
                command = script[start:p]
                if p < len(script) and c == '%' and script[p] == '(':
                    p += 1
                    s = p
                    while p < len(script) and script[p] != ')':
                        if script[p] == '\\' and script[p + 1] == ')':
                            p += 1
                        p += 1
                    command += script[s:p]
                    p += 1

                option = ''
                if p < len(script) and script[p] == '[':
                    p += 1
                    s = p
                    while p < len(script) and script[p] != ']':
                        if script[p] == '\\' and script[p+1] == ']':
                            p += 1
                        p += 1
                    option = script[s:p]
                    p += 1

                if command == 'q' and option != '' and ',' in option:
                    if is_first_question:
                        self.question_record.clear()
                        is_first_question = False

                    svec = option.split(',')
                    if len(svec) == 1:
                        svec.append('')
                    slabel = svec[0]
                    sid = svec[1]
                    if sid.find('on') != 0 \
                            and sid.find('On') != 0 \
                            and sid.find('http://') != 0 \
                            and sid.find('https://') != 0 \
                            and sid.find('script:') != 0 \
                            and sid.find('\"script:') != 0:
                        count = len(self.question_record)
                        self.question_record[sid] = (count, slabel)

                        vec_id = []
                        if len(sid) == 0:
                            vec_id.append("")
                        else:
                            vec_id = sid.split('\\1')

                        byte1_dlmt = chr(1) + chr(0)
                        option = slabel + ',' + vec_id[0] + byte1_dlmt + slabel + byte1_dlmt + str(count)
                        for i in range(2, len(svec)):
                            option += ',' + svec[i]
                elif command == '0' or command == 'h':
                    last_speaker = 0
                elif command == '1' or command == 'u':
                    last_speaker = 1
                elif command == 'p' and self.are_digits(option):
                    last_speaker = int(option)
                    if last_speaker <= 1:
                        command = '0' if option == '0' else '1'
                        option = ''
                elif command == 's' and not option.isspace():
                    self.last_talk_exiting_surface[last_speaker] = int(option)
                elif len(command) == 2 and command[0] == 's' and self.is_digit(command[1]):
                    self.last_talk_exiting_surface[last_speaker] = command[1] - '0'

                if len(acum) > 0:
                    vec.append(('', acum))

                vec.append((c + command, '') if option == '' else (c + command, option))
                acum = ''

                if command not in ['0', '1', 'h', 'u', 'p', 'n', 'w', '_w', 'e']:
                    content = True
            else:
                content = True
                acum += c
        pass  # exit while

        if len(acum) > 0:
            vec.append(('', acum))

        if not content:
            return False

        self.tokens = vec
