import java.util.Scanner;
public class IT26101437Lab5Q2  {
    public static void main(String[] args) {
		
    Scanner input = new Scanner(System.in);
	
	 System.out.print("Enter the number: ");
     int num = input.nextInt();
	 
	switch (num) {
                case 0:
                    System.out.println("Prize: No Prize");
                    break;

                case 1:
                    System.out.println("Prize: Pen");
                    break;

                case 2:
                    System.out.println("Prize: Umbrella");
                    break;

                case 3:
                    System.out.println("Prize: Bag");
                    break;

                case 4:
                    System.out.println("Prize: Travelling Chair");
                    break;

                default:
                    System.out.println("Prize: Headphone");
                    break; 
	    }
		
    }
}
