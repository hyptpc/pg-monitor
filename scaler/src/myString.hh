#ifndef MYSTRING_
#define MYSTRING_

class myString{
public:
  static const int max_line_length_  = 1024;
  static const int max_param_length_ = 20;
  
  myString();
  ~myString();
  
  static          int myScanf(char* inBuf,
			      char* argBuf1, char* argBuf2,  char* argBuf3);
  static unsigned int myAtoi(char* str);

private:
  static int myGetArg(char* inBuf, int i, char* argBuf);

  myString(const myString& object);
  myString& operator =(const myString& object);
};

#endif
