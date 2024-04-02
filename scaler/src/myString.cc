#include"myString.hh"

#include<cstring>
#include<cstdlib>
#include<cstdio>
#include<ctype.h>

myString::myString()
{
  
}

myString::~myString()
{

}

int myString::myScanf(char* inBuf,
		      char* argBuf1, char* argBuf2,  char* argBuf3)
{
  int i=0;

  argBuf1[0]='\0';
  argBuf2[0]='\0';
  argBuf3[0]='\0';

  if((i=myGetArg(inBuf, i, argBuf1))>0){
    if((i=myGetArg(inBuf, i, argBuf2))>0){
      return myGetArg(inBuf, i, argBuf3);
    }else{
      return i;
    }
  }else{
    return i;
  }
  return i;
}

unsigned int myString::myAtoi(char* str)
{
  char temp[256];
  int i=0, j=0, value=0, endProc=0;
  strcpy(temp,str);

  if((temp[i]=='0')||isblank(temp[i])) i++;
  if((temp[i]=='x')||(temp[i]=='X')){
    i++;
    j++;
    while((endProc==0)&&(temp[i]!='\0')){
      if(isdigit(temp[i])){
	value=value*16;
	value+=temp[i]-'0';
	i++;
      }else if(isxdigit(temp[i])){
	value=value*16;

	if(isupper(temp[i])){
	  value+=temp[i]-'A'+10;
	}else{
	  value+=temp[i]-'a'+10;
	}
	i++;
      }else{
	endProc=1;
	//	puts("endProc");
      }
    }
    if(j>8){
      puts("Error: too large value is detected.");
      return 0xFFFFFFFF;
    }
  }else{
    while(isdigit(temp[i])){
      value=value*10;
      value+=temp[i]-'0';
      i++;
      j++;
      if(j>10){
	puts("Error: too large value is detected.");
	return 0xFFFFFFFF;
      }
    }
  }

  return value;
}

int myString::myGetArg(char* inBuf, int i, char* argBuf)
{
  int j;

  while(i<max_line_length_){
    if(isblank(inBuf[i])){
      i++;
    }else if(iscntrl(inBuf[i])){
      return 0;
    }else {
      break;
    }
  }

  for(j=0;j<max_param_length_;j++){
    if(i<max_line_length_){
      if(isblank(inBuf[i])){
	argBuf[j]='\0';

      }else if(iscntrl(inBuf[i])){
	argBuf[j]='\0';
	return 0;
      }else{
	argBuf[j]=inBuf[i];
	i++;
      }
    }else{
      return -1;
    }
  }
  return i;
}
