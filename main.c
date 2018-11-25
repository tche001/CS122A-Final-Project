#include <avr/io.h>

//FreeRTOS include files
#include "FreeRTOS.h"
#include "task.h"
#include "croutine.h"
#include "usart_ATmega1284.h"

unsigned char pattern = 0x01;
unsigned char row = 0x10;
unsigned short joystick = 0;
unsigned short temp = 0;
enum LRStates{leftRight, upDown} state;
enum LEDMatrixStates{display} LEDstate;


// Pins on PORTA are used as input for A2D conversion
// The Default Channel is 0 (PA0)
// The value of pinNum determines the pin on PORTA used for A2D conversion
// Valid values range between 0 and 7, where the value represents the desired pin for A2D conversion
void Set_A2D_Pin(unsigned char pinNum)
{
	ADMUX = (pinNum <= 0x07) ? pinNum : ADMUX;
	// Allow channel to stabilize
	static unsigned char i = 0;
	for(i = 0; i < 15; ++i){asm("nop");}
}

void A2D_init()
{
	ADCSRA |= (1 << ADEN) | (1 << ADSC) | (1 << ADATE);
	//ADEN: Enables analog-to-digital conversion
	//ADSC: Starts analog-to-digital conversion
	//ADATE: Enables auto-triggering, allowing for constant analog to digital conversions.
}

void convert()
{
	ADCSRA |=(1<<ADSC);//start ADC conversion
	while ( !(ADCSRA & (1<<ADIF)));//wait till ADC conversion
	
}

void LR_Tick()
{
	switch(state)
	{
		case leftRight:
			Set_A2D_Pin(0x00);
			convert();
			joystick = ADC;
			if(joystick < 350)
			{
				if( USART_IsSendReady(0) )
				{
					USART_Send(0x01,0);
					PORTC=0x01;
					USART_Flush(0);
				}
			}
			else if(joystick > 700)
			{
				if( USART_IsSendReady(0) )
				{
					USART_Send(0x02,0);
					PORTC=0x02;
					USART_Flush(0);
				}
			}
			else{
				if( USART_IsSendReady(0) )
				{
					USART_Send(0x00,0);
					PORTC=0x00;
					USART_Flush(0);
				}
			}
			state = upDown;
			break;
		case upDown:
			Set_A2D_Pin(0x01);
			convert();
			temp = ADC;
			if(temp < 350)
			{
				if( USART_IsSendReady(0) )
				{
					USART_Send(0x04,0);
					PORTC=0x04;
					USART_Flush(0);
				}
			}
			else if(temp > 700)
			{
				if( USART_IsSendReady(0) )
				{
					USART_Send(0x08,0);
					PORTC=0x08;
					USART_Flush(0);
				}
			}
			else{
				if( USART_IsSendReady(0) )
				{
					USART_Send(0x00,0);
					PORTC=0x00;
					USART_Flush(0);
				}
			}
			state = leftRight;
			break;
		default:
			break;
	}
}

void LR_Task()
{
	state = leftRight;
	for(;;)
	{
		LR_Tick();
		vTaskDelay(250);
	}
}

void StartShiftPulse(unsigned portBASE_TYPE Priority)
{
	xTaskCreate(LR_Task, (signed portCHAR *) "LR_Task", configMINIMAL_STACK_SIZE, NULL, Priority, NULL);
}

int main(void)
{
	DDRA = 0x00; PORTA = 0xFF;
	DDRC = 0xFF; PORTC = 0x00;
	DDRD = 0xFF; PORTD = 0x00;
	A2D_init();
	initUSART(0);
	StartShiftPulse(1);
	vTaskStartScheduler();
	return 0;
}