import libmodem
from string import *
import baseconvert
import sys

class libSMS(libmodem.Modem):
    def __init__(self, dev, baud, timeoutnya):
        libmodem.Modem.__init__(self, dev, baud, timeoutnya)
        self.maxSMS = 10
        try:
           r = self.send("AT+CPMS?", "OK")
           # +CPMS: "SM",0,30,"SM",0,30
           atcpms = True
        except:
           atcpms = False

        if atcpms:
           if libmodem.debug:
               print r
           if r[0] == 2:
               # was
               # self.maxSMS = int(split(r[1],",")[2])
               # 2008-12-30
               # 4 baris dibawah ini ditambahin utk make sure kalo
               # hasil dari AT+CPMS? ini invalid
               # maka diberikan default 10
               try:
                  self.maxSMS = int(split(r[1],",")[2])
               except:
                  self.maxSMS = 10
               if libmodem.debug:
                  print "self.maxSMS", self.maxSMS

        #self.send("AT+CMGF=0","OK") # pdu
        #self.send("AT+CMGF=1","OK") # text

    def readSMSPDU(self,i):
        self.send("AT+CMGF=0","OK") # pdu
        r = self.send("AT+CMGR="+str(i), "OK")
        if r[0] == 2 and r[1] != "":
            if libmodem.debug:
                print r
            # (2, '+CMGR: 1,,38\r\n059126181642440C9126181694109400007001503174948215050A03000E089F6B10B98C7629A669B8CBE502\r\n')
            # todo : kalo ada --- +CMTI: "SM",1 --- skip aja
            rlsplit = split(r[1],"\r\n")

            rlsplit = rlsplit[1]
            rlsplit2 = []
            for i in range(len(rlsplit)):
                if i != 0 and i % 2 == 0:
                   rlsplit2.append(rlsplit[i-2:i])
                if i == len(rlsplit) - 1:
                   rlsplit2.append(rlsplit[len(rlsplit)-2:len(rlsplit)])
            print rlsplit2
            #smsclen = baseconvert.baseconvert(rlsplit2[0],baseconvert.BASE16,baseconvert.BASE10)
            smsclen = baseconvert.hex2dec(rlsplit2[0])
            print "smsclen", smsclen
            smsc_toa = rlsplit2[1]
            smsc = ""
            for i in range(int(smsclen)-1):
                smsc = smsc + rlsplit2[i+2][1] + rlsplit2[i+2][0]
            if smsc_toa == "91":
               smsc = "+" + smsc
            if smsc[-1:] == "F":
               smsc = smsc[:-1]
            #print smsc

            #senderlen = baseconvert.baseconvert(rlsplit2[int(smsclen)+2],baseconvert.BASE16,baseconvert.BASE10)
            senderlen = baseconvert.hex2dec(rlsplit2[int(smsclen)+2])
            print "senderlen", senderlen
            print "senderlen2", (int(senderlen)-(int(senderlen)/2))
            sender_toa = rlsplit2[int(smsclen)+3]
            sender = ""
            for i in range(int(senderlen)-(int(senderlen)/2)):
                sender = sender + rlsplit2[i+int(smsclen)+4][1] + rlsplit2[i+int(smsclen)+4][0]
            print "sender_toa", sender_toa
            if sender_toa == "91":
               sender = "+" + sender
               if sender[-1:] == "F":
                  sender = sender[:-1]
                  senderlen = (int(senderlen)-(int(senderlen)/2)) + 6
            elif sender_toa == "A1":
               # national number
               # baru ditambahin 2007-12-17, gara2 error pas baca smspdu dari esia
               if sender[-1:] == "F":
                  sender = sender[:-1]
                  senderlen = (int(senderlen)-(int(senderlen)/2)) + 6
            elif sender_toa == "D0":
               sender = ""
               for i in range(int(senderlen)-(int(senderlen)/2)):
                   sender = sender + rlsplit2[i+int(smsclen)+4]
               import pdu
               sender = pdu.pdu2text(sender)
               senderlen = int(senderlen)-2

            #print sender

            tp_dcs = rlsplit2[int(smsclen)+int(senderlen)-1]

            rectimestamp = ""
            for i in range(7):
                rectimestamp = rectimestamp + rlsplit2[int(smsclen)+int(senderlen)+i][1] + rlsplit2[int(smsclen)+int(senderlen)+i][0]
            #print rectimestamp
            #print rectimestamp[0:2]+"/"+rectimestamp[2:4]+"/"+rectimestamp[4:6]
            #print rectimestamp[6:8]+":"+rectimestamp[8:10]+":"+rectimestamp[10:12]

            a =  rlsplit2[int(smsclen)+int(senderlen)+8:]
            b = ""
            for i in range(len(a)):
                b = b + a[i]
            #print b
            import pdu

            sms = {}
            sms["flag"] = ""
            sms["smsc"] = smsc
            sms["sender"] = sender
            sms["recdate"] = rectimestamp[0:2]+"/"+rectimestamp[2:4]+"/"+rectimestamp[4:6]
            sms["rectime"] = rectimestamp[6:8]+":"+rectimestamp[8:10]+":"+rectimestamp[10:12]
            sms["message"] = ""
            if tp_dcs == "00":
               # 7bit
               if b != "":
                  sms["message"] = pdu.pdu2text(b)
               else:
                  sms["message"] = ""
            elif tp_dcs == "04":
               # 8bit
               sms["message"] = ""
               for i in range(len(a)):
                   #b = baseconvert.baseconvert(a[i],baseconvert.BASE16,baseconvert.BASE10)
                   b = baseconvert.hex2dec(a[i])
                   if b == "":
                      b = 0
                   sms["message"] = sms["message"] + chr(int(b))
            if libmodem.debug:
                print sms
            return (True,sms)
        else:
            return (False,None)

    def readSMS(self,i):
        self.send("AT+CMGF=1","OK") # text
        r = self.send("AT+CMGR="+str(i), "OK")
        if r[0] == 2 and r[1] != "":
            if libmodem.debug:
                print r
            # '+CMGR: "REC READ","+628170267347",,"07/09/28,14:14:10+28"\r\nIni tes\r\n'
            rlsplit = split(r[1],",")
            sms = {}
            sms["flag"] = strip(rlsplit[0])[8:-1] # '+CMGR: "REC READ"'
            sms["sender"] = strip(rlsplit[1])[1:-1] # '"TSEL-ARE"'
            sms["recdate"] = strip(rlsplit[3])[1:] # '"07/08/19'
            sms["rectime"] = strip(rlsplit[4])[:8] # '14:36:38+32"'
            sms["message"] = strip(r[1][r[1].index("\r\n")+2:])
            if libmodem.debug:
                print sms
            return (True,sms)
        else:
            return (False,None)

    def delSMS(self,i):
        r = self.send("AT+CMGD="+str(i), "OK")
        if r[0] == 2:
            if libmodem.debug:
                print r
            return True
        else:
            return False

    def sendSMS(self,number, message):
        self.send("AT+CMGF=1","OK") # text
        #self.ser.write('AT+CMGS="%s"\r' % number)
        #self.ser.readline()
        oldEndCommand = self.endCommand
        oldEndResponse = self.endResponse
        self.endResponse = ""
        self.send('AT+CMGS="%s"' % number, "> ")
        self.endResponse = oldEndResponse
        self.endCommand = ""
        self.send("%s\x1A" % message, "OK")
        self.endCommand = oldEndCommand

    def sendSMSPDU(self,number, message):
        len_smsc_info = "00" # Length of SMSC information
        fo = "31" # First Octet
        tp_mr = "00" # TP-MR TP-Message-Reference
        #tp_dal =  zfill(baseconvert.baseconvert(len(number) - 1,baseconvert.BASE10,baseconvert.BASE16),2) # TP-DA Dest. Address Length (number)
        tp_dal =  zfill(baseconvert.dec2hex(len(number) - 1),2) # TP-DA Dest. Address Length (number)
        #print tp_dal
        tp_dat = "91" # TP-DA Type of Dest. Address (international)
        tp_da = number[1:len(number)] # TP-DA Dest. Address (phone number)
        if (len(number) - 1) % 2 == 1:
           tp_da = number[1:len(number)] + "F"
        #print tp_da
        new_tp_da = ""
        for i in range(len(tp_da)):
            if i != 0 and i % 2 == 1:
               new_tp_da = new_tp_da + tp_da[i] + tp_da[i-1]
        #print new_tp_da
        tp_pid = "00" # TP-PID TP-Protocol-Identifier
        tp_dcs = "04" # TP-DCS TP-Data-Coding-Scheme 04 = 8bit, 00 = 7bit
        tp_vp = "00" # TP-VP TP-Validity-Period 5 minutes
        #tp_udl = zfill(baseconvert.baseconvert(len(message),baseconvert.BASE10,baseconvert.BASE16),2) # TP-UDL TP-User-Data-Length
        tp_udl = zfill(baseconvert.dec2hex(len(message)),2) # TP-UDL TP-User-Data-Length
        if libmodem.debug:
           print tp_udl
        tp_ud = "" # TP-UD TP-User-Data
        for i in range(len(message)):
            #print message[i], ord(message[i]), zfill(baseconvert.baseconvert(ord(message[i]),baseconvert.BASE10,baseconvert.BASE16),2)
            #tp_ud = tp_ud + zfill(baseconvert.baseconvert(ord(message[i]),baseconvert.BASE10,baseconvert.BASE16),2)
            tp_ud = tp_ud + zfill(baseconvert.dec2hex(ord(message[i])),2)
        if libmodem.debug:
           print tp_ud
        sent = len_smsc_info+fo+tp_mr+tp_dal+tp_dat+new_tp_da+tp_pid+tp_dcs+tp_vp+tp_udl+tp_ud

        if libmodem.debug:
           print 'AT+CMGS=%d' % ((len(sent)-1) / 2)
           print sent

        self.send("AT+CMGF=0","OK") # pdu
        oldEndCommand = self.endCommand
        oldEndResponse = self.endResponse
        self.endResponse = ""
        self.send('AT+CMGS=%d' % ((len(sent)-1) / 2), "> ")
        self.endResponse = oldEndResponse
        self.endCommand = ""
        r = self.send("%s\x1A" % sent, "OK")
        self.endCommand = oldEndCommand
        return r




if __name__ == '__main__':
    #a = libSMS("/dev/ttya01", 2400, 120)
    #print a.sendSMS("+62123456789", "test\ntest aja")
    #print a.sendSMSPDU("+62123456789", "test\ntest aja")
    #print a.readSMSPDU(10)
    #print a.readSMS(10)
    #print a.readSMSPDU(3)
    #print a.readSMS(3)
    #for i in range(a.maxSMS):
    #for i in range(10):
        #print a.readSMSPDU(i+1)
        #print a.readSMS(i+1)
    #a.close()
    #a = libSMS("/dev/ttya10", 2400, 120)
    #for i in range(5):
    #    print a.readSMS(i+1)
    #a.close()
