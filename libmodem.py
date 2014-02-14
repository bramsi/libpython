import serial
import time
import sys
from string import *
debug = True

class Modem:
    def __init__(self, dev, baud, timeoutnya):
        try:
            self.ser = serial.Serial(dev, baud, timeout=1)
        except:
            e = sys.exc_info()[1]
            raise "Error on serial: %s" % e
        self.timeoutnya = timeoutnya
        self.endCommand = "\r"
        self.endResponse = "\r\n"

        resetx = self.reset()
        if not resetx[0]:
           raise "Error on reset(): %s" % resetx[1]

        testx = self.test()
        if not testx[0]:
           raise "Error on test(): %s" % testx[1]

        #self.test2() # gsm aja yg punya cpas

    def reset(self):
        r = self.send("ATZ", "OK")
        if r[0] == 2:
            return (True, None)
        else:
            return (False, r[1])

    def test(self):
        r = self.send("AT", "OK")
        if r[0] == 2:
            return (True, None)
        else:
            return (False, r[1])

    def test2(self):
        r = self.send("AT+CPAS", "OK")
        # '+CPAS: 0\r\n'
        cpas = int(split(strip(r[1]), " ")[1])
        if r[0] == 2 and cpas == 0:
            return (True, None)
        else:
            return (False, r[1])

    def send(self, s, ex):
        self.ser.flush()
        self.ser.flushOutput()
        self.ser.flushInput()
        self.ser.write(s+self.endCommand)
        retval = 0
        retvalStr = ""
        resp = ""
        if debug:
            print s
        for i in range(self.timeoutnya):
            rl = self.ser.readline()
            if debug:
                print rl, i
            if strip(rl) == strip(s) and i == 0:
                # kalo response pertama kali sama dengan perintah yg dikirim
                # do nothing
                pass
            elif strip(rl)[:6] == "+CMTI:" or strip(rl)[:5] == "CMTI:" or strip(rl)[:4] == "MTI:":
                # abaikan kalo +CMTI: "SM",1
                pass
            elif strip(rl) == "ERROR" or strip(rl)[:11] == "+CMS ERROR:":
                # kalo response ERROR/+CMS ERROR, berhenti
                retval = 1 # ERROR
                retvalStr = "AT Command return ERROR (%s)" % strip(rl)
                break
            elif strip(rl) in ["NO ANSWER", "NO CARRIER", "BUSY", "NO DIAL TONE", "NO DIALTONE"]:
                # kalo response sda, berhenti
                retval = 4 # "NO ANSWER", "NO CARRIER", "BUSY", "NO DIAL TONE"
                retvalStr = "AT Command return %s" % strip(rl)
                break
            else:
                if rl == ex+self.endResponse:
                    retval = 2 # dpt response sesuai dengan permintaan
                    break
                else:
                    if strip(rl) != "":
                        resp = resp + rl
                # khusus utk kirim sms, response "> "
                #if s[:7] == "AT+CMGS" and ex == "> ":
                #    if rl == ex:
                #        retval = 2 # dpt response sesuai dengan permintaan
                #        break
                #    else:
                #        if strip(rl) != "":
                #            resp = resp + rl
                #else:
                #    if rl == ex+self.endResponse:
                #        retval = 2 # dpt response sesuai dengan permintaan
                #        break
                #    else:
                #        if strip(rl) != "":
                #            resp = resp + rl
        if i == self.timeoutnya - 1:
            retval = 3 # timeout
            retvalStr = "AT Command timeout"
        if retval == 2:
            return (retval, resp)
        else:
            return (retval, retvalStr, resp)



    def close(self):
        self.ser.close()

if __name__ == '__main__':
    try:
       a = Modem("/dev/ttya13", 2400, 120)
    except:
       raise sys.exc_info()[0]
    print a.send("AT","OK")
    a.close()
