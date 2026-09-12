import java.util.Scanner;
  
   public class IT26101437Lab5Q1 {
    public static void main(String[] args) {
	Scanner input = new Scanner(System.in);
    int number,smallest,largest;	
     
	System.out.println("Enter the first integer:");
	number = input.nextInt();
	
	System.out.println("Enter the second integer:");
	int number1 = input.nextInt();
	
	System.out.println("Enter the third integer:");
	int number2 = input.nextInt();
	
	System.out.println("USER INPUTS:" + number +"  " + number1+"  " + number2+"  ");
	
	smallest = number1;
	
	if(number<smallest)
	{		
      smallest = number;
	}

    if(number2<smallest)
	{
	  smallest = number2;	
	}
    System.out.println("smallest number is:"+smallest);

    largest = number1;
	
	if(number>largest)
	{		
      largest = number;
	}

    if(number2>largest)
	{
	  largest = number2;	
	}
    System.out.println("Largest number is:"+largest);	
	
   }
}   
        	