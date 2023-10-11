/*
Base code for gsm alarm firmware

to be updated with control commands over serial interface
*/

#include <SoftwareSerial.h>;

SoftwareSerial SIM900(7, 8); // configure software sim900 serial interface

char incoming_char=0; //incoming sim900 chars
int exitCnt = 0;

void setup()
{
    SIM900.begin(19200); //sim speed SIM
    delay(25000); //network finding delay
    Serial.begin(19200); //arduino serial comm
    Serial.println("OK"); //heart beat
}

// call to local phone
void make_call()
{
    SIM900.println("ATD 33XXXXXXXX;"); //phone
    delay(100);
    SIM900.println();
    delay(30000); // wait for 30 seconds...
    SIM900.println("ATH"); // hang
    delay(1000);
}

//SMS function
void sms_send()
{
    SIM900.print("AT+CMGF=1\r"); // AT command to send SMS message
    delay(100);
    SIM900.println("AT+CMGS=\"33XXXXXXXX\""); // recipient's mobile number, in international format
    delay(100);
    SIM900.println("Saludos desde HetPro"); // message to send
    delay(100);
    SIM900.println((char)26); // End AT command with a ^Z, ASCII code 26 //Comando de finalizacion
    delay(100);
    SIM900.println();
    delay(5000); // wait time
    Serial.println("SMS sent successfully");
}

void sms_wait()
{
    exitCnt = 1;
    while(exitCnt==1)
    {
        if(SIM900.available()>0)
        {
            incoming_char=SIM900.read(); //Get the character from the cellular serial port.
            Serial.print(incoming_char); //Print the incoming character to the terminal.
            exitCnt = 0;
        }
    }
}
void receive_sms_mode()
{
    //configure mode message reception
    SIM900.print("AT+CMGF=1\r"); // set SMS mode to text
    delay(100);
    SIM900.print("AT+CNMI=2,2,0,0,0\r");

    // blurt out contents of new SMS upon receipt to the GSM shield's serial out
    delay(1000);
}

void loop()
{
    make_call(); //do a call
    sms_send(); //send message
    receive_sms_mode();
    for(;;)
    {
        if(SIM900.available()>0)
        {
            incoming_char=SIM900.read(); //Get the character from the cellular serial port.
            Serial.print(incoming_char); //Print the incoming character to the terminal.
        }
        if(Serial.available()>0)
        {
            if(Serial.read() == 'A') break;
        }
    }
    Serial.println("OK-2");

    delay(100);
    SIM900.println();
    delay(30000);
    while(1); //wait forever, end of demo

}