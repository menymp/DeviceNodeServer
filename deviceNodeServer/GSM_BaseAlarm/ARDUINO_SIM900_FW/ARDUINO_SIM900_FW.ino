/*
Base code for gsm alarm firmware

to be updated with control commands over serial interface
*/

#include <SoftwareSerial.h>;
#include <String.h>

#define CALL_NUMBER_LEN  10

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
void sms_send(char * number, char * msg)
{
	const char numberBuff[20]{};
	
	strcat(numberBuff, "AT+CMGS=\"");
	strcat(numberBuff, number);
	strcat(numberBuff, "\"");
	
    SIM900.print("AT+CMGF=1\r"); // AT command to send SMS message
    delay(100);
    SIM900.println(numberBuff); // recipient's mobile number, in international format
    delay(100);
    SIM900.println(msg); // message to send
    delay(100);
    SIM900.println((char)26); // End AT command with a ^Z, ASCII code 26
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

void parse_serial_command()
{
	char inputCmdBuffer[20]{};
	
	Serial.readBytesUntil(NULL ,inputBuffer ,sizeof(inputBuffer));
	
	if(!strcmp(inputCmdBuffer, "SMSSEND"))
	{
		char inputNumber[30]{};
		char inputMsg[100]{};
		
		Serial.readBytesUntil(NULL ,inputNumber ,sizeof(inputNumber));
		Serial.readBytesUntil(NULL ,inputMsg ,sizeof(inputMsg));
		if(strlen(inputNumber) != CALL_NUMBER_LEN)
		{
			Serial.println("Error:Wrong Number Len!");
			return;
		}
		if(strlen(inputMsg) == 0)
		{
			Serial.println("Error:Empy Message!");
			return;
		}
		/*ToDo: check if there is a way to read the sim state and return error*/
		sms_send(inputNumber, inputMsg);
		Serial.println("SUCCESS");
	}
	String serialCommand = Serial.readBytesUntil(NULL ,inputBuffer ,sizeof(inputBuffer));
}

void loop()
{
	parse_serial_command();
	/*
    sms_send(); //send message
    receive_sms_mode();
    for(;;)
    {
        if(SIM900.available()>0)
        {
            incoming_char=SIM900.read();
            Serial.print(incoming_char);
        }
        if(Serial.available()>0)
        {
            if(Serial.read() == 'A') break;
        }
    }
	*/
}