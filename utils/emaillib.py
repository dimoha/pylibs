# -*- coding: utf-8 -*-
import socket, os
from pylibs.utils.text import toUnicode
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.mime.multipart import MIMEMultipart
from email.Utils import COMMASPACE, formatdate
from email import Encoders

def sendmail(to_email, email_subject, email_body, from_email=None):
    if from_email is None:
        from_email = "info@%s" % socket.gethostname()
    sendmail_location = "/usr/sbin/sendmail"
    p = os.popen("%s -t" % sendmail_location, "w")
    p.write("From: %s\n" % from_email)
    p.write("To: %s\n" % to_email)
    p.write("Content-Type: text/plain; charset=windows-1251\n")
    p.write("Subject: %s\n" % email_subject.encode("windows-1251"))
    p.write("\n")  # blank line separating headers from body
    p.write(toUnicode(email_body).encode("windows-1251"))
    p.close()


def send_mail(to_email, email_subject, email_body,
              from_email=None, files=[], attaches=[]):
    """ Функция для отправки писем с аттачами """
    assert type(to_email) == list
    assert type(files) == list
    if from_email is None:
        from_email = "info@%s" % socket.gethostname()
    sendmail_location = "/usr/sbin/sendmail"
    if isinstance(email_body, unicode):
        email_body = email_body.encode('utf-8')
    if isinstance(email_subject, unicode):
        email_subject = email_subject.encode('utf-8')
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = COMMASPACE.join(to_email)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = email_subject
    msg.attach(MIMEText(email_body, 'html', 'utf-8'))
    for k,items in enumerate([files, attaches]):
        is_files = True if k==0 else False
        for item in items:
            part = MIMEBase('application', "octet-stream")
            attach_body = open(item, "r").read() if is_files else item['body']
            attach_name = os.path.basename(item) if is_files else item['name']
            part.set_payload(attach_body)
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' %
                        attach_name)
            msg.attach(part)
    p = os.popen("%s -t" % sendmail_location, "w")
    p.write(msg.as_string())
    p.close()
