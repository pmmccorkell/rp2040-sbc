// Test program for WSE-PROJ-SBC
// J Bradshaw
// 20140912
#include "mbed.h"
#include "mbedWSEsbc.h"

//---------- Command Display ------------------------------
void display_commands(void){
    pc.printf("Commands are as follows\r\n");
    pc.printf("adc CH - CH is channel from 0-7. Returns voltage on adc channel.\r\n");
    pc.printf("daca - sends voltage to DACA - Vref may vary depending on voltage source.\r\n");
    pc.printf("dacb - sends voltage to DACB - Vref may vary depending on voltage source.\r\n");
    pc.printf("enc CH NUM - loads NUM into encoder channel CH (ex. enc 2 2365).\r\n");
    pc.printf("enc1 - returns value of encoder channel 1\r\n");
    pc.printf("enc1z - zeros encoder channel 1\r\n");
    pc.printf("enc2 - returns value of encoder channel 2\r\n");
    pc.printf("enc2z - zeros encoder channel 2\r\n");
    pc.printf("mot1 VALUE - generates PWM and controls direction bits on motor port 1 (VALUE is from -1.0 to 1.0).\r\n");
    pc.printf("mot2 VALUE - generates PWM and controls direction bits on motor port 2 (VALUE is from -1.0 to 1.0).\r\n");
    pc.printf("\r\n");
}
//------------------- MAIN --------------------------------
int main()
{
    long enc1, enc2;
    char last_cmd[20];
    char cmd_str[30];
    
    mbedWSEsbcInit(9600);  //Initialize the mbed WSE Project SBC
                                
    while(pc.readable())
        char c = pc.getc();     //read character to clear buffer

    t.reset(); // zero timer        
        
    pc.printf("Press ? for command set\r\n");
    
    while(1){
        if(pc.readable()){            //if data in receive buffer
        
//            if(char c = pc.getc();
                char c = pc.scanf("%s", cmd_str);//read the string
                
                if(!strcmp(cmd_str, "adc")){
                    int i;
                    pc.scanf("%d", &i);//read the string
                    if(i<0)
                        i=0;
                    if(i>7)
                        i=7;
    
                    float volts = read_max1270_volts(i, 1, 1);    //chan0, range=1:10V, bipolar=1:+/-10V                       
                    pc.printf("adc%d=%.2f\r\n",i, volts);                
                } 
                
                //Write Voltage to dac channel A - REF Dependant
                else if(!strcmp(cmd_str, "daca")){
                    float voltsA;
                    pc.scanf("%f", &voltsA);//read the string
                    write_max522(1, voltsA);
                    pc.printf("dacA=%.2f\r\n", voltsA);
                }
    
                //Write Voltage to dac channel B - REF Dependant
                else if(!strcmp(cmd_str, "dacb")){
                    float voltsB;
                    pc.scanf("%f", &voltsB);//read the string
                    write_max522(2, voltsB);
                    pc.printf("dacB=%.2f\r\n", voltsB);
                }
                
                //Write to encoder channel (ex. "enc 2 34700\r")
                else if(!strcmp(cmd_str, "enc")){
                    int chan;
                    pc.scanf("%d", &chan);//read the string for the channel
                    long counts;
                    pc.scanf("%d", &counts);//read the string for counts
                    LS7366_write_DTR(chan, counts);
                    long enc = LS7366_read_counter(chan);        
                    pc.printf("enc%d = %d\r\n", chan, enc);
                }
                
                else if(!strcmp(cmd_str, "enc1")){
                    enc1 = LS7366_read_counter(1);        
                    pc.printf("enc1 = %d\r\n", enc1);
                }  
                else if(!strcmp(cmd_str, "enc1z")){
                    LS7366_write_DTR(1,0);    //zero encoder channel 1      
                    LS7366_reset_counter(1);        
                    enc1 = LS7366_read_counter(1);        
                    pc.printf("enc1 = %d\r\n", enc1);
                }
                
                else if(!strcmp(cmd_str, "enc2")){
                    enc2 = LS7366_read_counter(2);
                    pc.printf("enc2 = %d\r\n", enc2);
                }
                else if(!strcmp(cmd_str, "enc2z")){
                    LS7366_write_DTR(2,0);    //zero encoder channel 1      
                    LS7366_reset_counter(2);        
                    enc2 = LS7366_read_counter(2);        
                    pc.printf("enc2 = %d\r\n", enc2);
                }                           
                
                else if(!strcmp(cmd_str, "mot1")){
                    float pwm1;
                    pc.scanf("%f", &pwm1);//read the string
                    mot_control(1, pwm1);
                    pc.printf("pwm1=%.2f\r\n", pwm1);
                }
                else if(!strcmp(cmd_str, "mot2")){
                    float pwm2;
                    pc.scanf("%f", &pwm2);//read the string
                    mot_control(2, pwm2);
                    pc.printf("pwm2=%.2f\r\n", pwm2);
                }
                
                else if(!strcmp(cmd_str, "?")){
                    display_commands();
                }
                
                else{
                    pc.printf("Unknown Command\r\n");       
                }
                
                strcpy(last_cmd, cmd_str);         
                //pc.printf("Message Error\r\n");
            }                    
        led3=!led3;
            //pc.printf("T=%.2f %.2f %.2f %d  %d  %.2f\r\n", t.read(), adc0, adc1, enc1, enc2, voltsA);
            //xbee.printf("T=%.2f %.2f %.2f %d  %d  %.2f\r\n", t.read(), adc0, adc1, enc1, enc2, voltsA);        
        wait(.02);
    }//while(1)                        
}//main
