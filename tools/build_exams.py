"""Generate backend/exams/data/*.json question banks.

Each question is (text, correct answer, [three wrong answers], explanation shown after a wrong answer).
Answer positions are shuffled here (fixed seed) and again for every attempt on the server.
Questions are based on the lessons in courses/*.docx.
"""
import json
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "backend" / "exams" / "data"

WORD = [
    ("A computer has two main parts. What are they?", "Hardware and software", ["Keyboard and screen", "Windows and Linux", "Files and folders"], "Hardware is the parts you can touch. Software is the programs that run on it."),
    ("Which of these is computer hardware?", "Keyboard", ["Microsoft Word", "Windows", "A Word document"], "The keyboard is a physical part you can touch, so it is hardware."),
    ("Which of these is software?", "Microsoft Word", ["Keyboard", "Screen", "Mouse"], "Microsoft Word is a program. Programs are software."),
    ("What is the main software that manages the computer's hardware and other software?", "The operating system", ["A driver", "A folder", "The keyboard"], "The operating system (for example Windows, macOS or Linux) manages the hardware and the other software."),
    ("Which key adds a space between words?", "The spacebar", ["Enter", "Backspace", "Shift"], "Press the spacebar, the long horizontal key at the bottom of the keyboard."),
    ("Which key starts a new line or paragraph?", "Enter", ["The spacebar", "Shift", "Ctrl"], "Press the Enter key to start a new line or paragraph."),
    ("When you save a document, what do you type in the File name field?", "A name for your document", ["Your password", "The font name", "The page number"], "You give the document a name so you can find it later."),
    ("Which keys move the cursor up, down, left and right?", "The arrow keys", ["The function keys", "The number keys", "Caps Lock"], "The arrow keys move the cursor around your text."),
    ("Before you change the font of text you already typed, what must you do first?", "Select the text", ["Save the file", "Insert a table", "Turn off the computer"], "Formatting is applied to the text you have selected."),
    ("Besides the dropdown list, how can you change the font size?", "Type a number in the Font Size box and press Enter", ["Press Ctrl + Z", "Click Blank Page", "Use the Eraser"], "You can type the size directly into the Font Size box and press Enter."),
    ("Which shortcut makes selected text bold?", "Ctrl + B", ["Ctrl + I", "Ctrl + U", "Ctrl + N"], "Ctrl + B = Bold."),
    ("Which shortcut makes selected text italic?", "Ctrl + I", ["Ctrl + B", "Ctrl + U", "Ctrl + L"], "Ctrl + I = Italic."),
    ("Which shortcut underlines selected text?", "Ctrl + U", ["Ctrl + B", "Ctrl + I", "Ctrl + S"], "Ctrl + U = Underline."),
    ("Which shortcut copies selected text?", "Ctrl + C", ["Ctrl + V", "Ctrl + X", "Ctrl + Z"], "Ctrl + C = Copy."),
    ("Which shortcut pastes copied text?", "Ctrl + V", ["Ctrl + C", "Ctrl + X", "Ctrl + A"], "Ctrl + V = Paste."),
    ("Which shortcut cuts selected text?", "Ctrl + X", ["Ctrl + C", "Ctrl + V", "Ctrl + S"], "Ctrl + X = Cut."),
    ("Which shortcut undoes your last action?", "Ctrl + Z", ["Ctrl + Y", "Ctrl + A", "Ctrl + F"], "Ctrl + Z = Undo the last action."),
    ("Which shortcut selects all the text in the document?", "Ctrl + A", ["Ctrl + S", "Ctrl + F", "Ctrl + N"], "Ctrl + A = Select all."),
    ("Which shortcut opens the Find box?", "Ctrl + F", ["Ctrl + S", "Ctrl + B", "Ctrl + N"], "Ctrl + F = Find."),
    ("Which shortcut saves the document?", "Ctrl + S", ["Ctrl + N", "Ctrl + F", "Ctrl + C"], "Ctrl + S = Save."),
    ("Which shortcut opens a new Word document?", "Ctrl + N", ["Ctrl + S", "Ctrl + O", "Ctrl + A"], "Ctrl + N = New document."),
    ("Which shortcut centres the text?", "Ctrl + E", ["Ctrl + L", "Ctrl + R", "Ctrl + J"], "Ctrl + E = Center. Ctrl + L is left, Ctrl + R is right and Ctrl + J is justify."),
    ("Which shortcut aligns the text to the left?", "Ctrl + L", ["Ctrl + E", "Ctrl + R", "Ctrl + J"], "Ctrl + L = Left."),
    ("Which shortcut justifies the text?", "Ctrl + J", ["Ctrl + L", "Ctrl + E", "Ctrl + R"], "Ctrl + J = Justify, so the lines are evenly spaced."),
    ("Which button changes the colour of text?", "Font Color (an A with a coloured underline)", ["Bold (B)", "Underline (U)", "Justify"], "The Font Color button looks like an A with a coloured underline."),
    ("Which Insert tab item creates colourful, decorative text?", "WordArt", ["Text Box", "Blank Page", "Page Number"], "WordArt creates colourful and decorative text."),
    ("Which Insert tab option adds an empty page?", "Blank Page", ["Cover Page", "Table", "Pictures"], "Blank Page adds a new empty page to your document."),
    ("How do you add page numbers to a document?", "Insert tab, then Page Number", ["Draw tab, then Pen", "Home tab, then Bullets", "Type each number yourself"], "Page numbers are added from the Insert tab with the Page Number button."),
    ("Which tab contains the Pen, Pencil, Highlighter and Eraser?", "Draw", ["Home", "Insert", "Layout"], "Drawing tools are on the Draw tab."),
    ("Which Draw tab tool removes a drawing you do not want?", "Eraser", ["Highlighter", "Pencil", "Pen"], "Select the Eraser and click the drawing to remove it."),
    ("To keep your files organised in My Documents you can make a:", "Folder", ["Border", "Cover page", "Highlight"], "A folder lets you group and find your saved files."),
    ("Which button puts dots in front of each item in a list?", "Bullets", ["Numbering", "Justify", "Sort"], "Bullets put a dot before every item. Numbering puts 1, 2, 3."),
]

EXCEL = [
    ("What is Microsoft Excel mainly used for?", "Organising information in tables, doing maths and making charts", ["Writing letters only", "Drawing pictures only", "Browsing the internet"], "Excel helps us organise information in tables, do mathematics and create charts."),
    ("A row in Excel goes:", "Across, from left to right", ["From top to bottom", "Diagonally", "Only in column A"], "Rows go across. Columns go from top to bottom."),
    ("A column in Excel goes:", "From top to bottom", ["Across, from left to right", "Diagonally", "Only in row 1"], "Columns go from top to bottom and are named with letters."),
    ("Cell A1 is where:", "Column A meets Row 1", ["Row A meets Column 1", "The formula bar starts", "The ribbon ends"], "A cell address is the column letter followed by the row number."),
    ("What is the Ribbon?", "The area at the top with the tabs and buttons", ["A single cell", "A chart", "The name of a worksheet"], "The Ribbon holds the tabs (Home, Insert, Data and more) and their buttons."),
    ("Every formula in Excel begins with which symbol?", "=", ["+", "#", "@"], "A formula always starts with the equals sign (=)."),
    ("A1 contains 10 and A2 contains 5. You type =A1+A2 in A3. What does Excel show?", "15", ["5", "10", "105"], "10 + 5 = 15."),
    ("B1 contains 20 and B2 contains 7. What does =B1-B2 show?", "13", ["27", "7", "140"], "20 - 7 = 13."),
    ("Which symbol does Excel use to multiply?", "*", ["x", "+", "/"], "Use * to multiply. Typing =B1xB2 is a mistake; the correct formula is =B1*B2."),
    ("Which symbol does Excel use to divide?", "/", ["*", "%", "-"], "Use / to divide."),
    ("C1 contains 6 and C2 contains 4. What does =C1*C2 show?", "24", ["10", "2", "64"], "6 x 4 = 24."),
    ("D1 contains 24 and D2 contains 6. What does =D1/D2 show?", "4", ["18", "30", "144"], "24 divided by 6 = 4."),
    ("What is the AutoSum symbol?", "Σ", ["π", "%", "#"], "AutoSum (Σ) quickly adds the numbers in a row or column."),
    ("A1 to A5 contain 10, 20, 30, 40 and 50. What does =SUM(A1:A5) show?", "150", ["50", "15", "100"], "SUM adds all the numbers: 10 + 20 + 30 + 40 + 50 = 150."),
    ("B1 to B4 contain 80, 70, 90 and 60. What does =AVERAGE(B1:B4) show?", "75", ["300", "70", "90"], "The total is 300, and 300 divided by 4 numbers is 75."),
    ("C1 to C5 contain 55, 88, 72, 91 and 67. What does =MIN(C1:C5) show?", "55", ["91", "72", "67"], "MIN finds the smallest number."),
    ("C1 to C5 contain 55, 88, 72, 91 and 67. What does =MAX(C1:C5) show?", "91", ["55", "88", "72"], "MAX finds the largest number."),
    ("What does the COUNT function do?", "Counts how many cells contain numbers", ["Adds the numbers", "Finds the average", "Finds the smallest number"], "COUNT tells you how many cells contain numbers."),
    ("Which of these is a correct formula?", "=SUM(A1:A5)", ["SUM(A1:A5)", "=A1+A", "=B1xB2"], "A formula needs the = sign, a real cell address, and * (not x) for multiplying."),
    ("Which shortcut copies the selected cell?", "Ctrl + C", ["Ctrl + X", "Ctrl + V", "Ctrl + F"], "Ctrl + C = Copy. Ctrl + X = Cut. Ctrl + V = Paste."),
    ("What does Cut and Paste do?", "Moves information from one place to another", ["Makes a copy and leaves the original", "Deletes the information forever", "Changes the font"], "Cut moves the information. Copy leaves the original where it is."),
    ("Which shortcut opens Replace, to change one word into another?", "Ctrl + H", ["Ctrl + S", "Ctrl + Z", "Ctrl + B"], "Ctrl + F is Find and Ctrl + H is Replace."),
    ("What does Conditional Formatting do?", "Changes the colour of a cell when it meets a rule", ["Adds up the numbers", "Sorts the names A to Z", "Inserts a picture"], "For example it can colour marks of 80 or more green and marks below 50 red."),
    ("Merge & Center is used to:", "Join cells and centre a title across columns", ["Add up two cells", "Delete a column", "Copy a table"], "Merge & Center makes one wide cell so a title sits in the middle of the table."),
    ("What does Wrap Text do?", "Makes long text fit inside the cell", ["Adds a border", "Changes the font colour", "Merges two cells"], "Wrap Text keeps the text inside the cell by using more lines."),
    ("Which tab do you use to insert a chart?", "Insert", ["Data", "Home", "Draw"], "Charts, pictures, shapes and tables are all on the Insert tab."),
    ("What is a chart for?", "Turning numbers into a picture so you can compare them quickly", ["Adding numbers", "Correcting spelling", "Saving the file"], "Charts help us compare information quickly."),
    ("Which tab has Sort and Filter?", "Data", ["Insert", "Draw", "Home"], "Sort and Filter are on the Data tab."),
    ("You filter the Class column and choose P5. What happens?", "Only the students in P5 are shown", ["The P5 students are deleted", "The names are sorted A to Z", "The column is removed"], "Filter hides the rows that do not match. The other rows are not deleted."),
    ("What does Sort A to Z do to a list of names?", "Puts the names in alphabetical order", ["Deletes repeated names", "Colours the names", "Counts the names"], "Sort A to Z arranges the names alphabetically."),
    ("What does a hyperlink do?", "Opens a website or another file when you click it", ["Adds two numbers", "Draws a shape", "Changes the row height"], "A hyperlink opens a website or another file."),
    ("Which Insert item lets you place words anywhere on the worksheet?", "Text Box", ["SmartArt", "Table", "Chart"], "A text box can be drawn anywhere and typed into."),
    ("What is SmartArt used for?", "Showing ideas with colourful diagrams", ["Adding numbers", "Sorting data", "Finding words"], "SmartArt turns ideas, like steps in a morning routine, into diagrams."),
    ("What does Format Painter do?", "Copies the look of one cell or heading to another", ["Adds up numbers", "Sorts a list", "Inserts a picture"], "Format Painter makes another heading look exactly the same as the first."),
]

SCRATCH = [
    ("What is Scratch?", "A programming language that uses blocks", ["A web browser", "A spreadsheet program", "A photo editor"], "Scratch lets you create games, stories and animations by joining blocks."),
    ("What is a sprite?", "A character or object in your project", ["The background of the Stage", "A sound", "A colour"], "A sprite is a character or object, such as the Scratch Cat."),
    ("What is the Stage?", "The place where your project happens", ["The place that stores the blocks", "A kind of sound", "A costume"], "The Stage is where you see your project run."),
    ("What does the Blocks Palette contain?", "The programming blocks", ["The sprites' costumes", "The saved projects", "The Stage backgrounds"], "You drag blocks out of the Blocks Palette."),
    ("What is the Script Area?", "Where you join blocks together", ["Where sprites are stored", "Where sounds are recorded", "Where the project is shown"], "You build your program by joining blocks in the Script Area."),
    ("What is a backdrop?", "The background of the Stage", ["A different look of a sprite", "A kind of block", "A sound effect"], "Backdrops change the Stage background."),
    ("What is a costume?", "A different appearance of a sprite", ["The Stage background", "A programming block", "A sound"], "Switching costumes makes a sprite look different, which is how animation works."),
    ("What colour are the Motion blocks?", "Blue", ["Yellow", "Orange", "Pink"], "Motion blocks are blue."),
    ("What colour are the Events blocks?", "Yellow", ["Blue", "Orange", "Purple"], "Events blocks are yellow."),
    ("What colour are the Control blocks?", "Orange", ["Blue", "Yellow", "Pink"], "Control blocks (wait, repeat, forever, if) are orange."),
    ("What colour are the Looks blocks?", "Purple", ["Blue", "Pink", "Orange"], "Looks blocks (say, think, size, costumes) are purple."),
    ("What colour are the Sound blocks?", "Pink", ["Purple", "Yellow", "Blue"], "Sound blocks are pink."),
    ("What are the X and Y positions of the centre of the Stage?", "x: 0, y: 0", ["x: 100, y: 100", "x: 180, y: 0", "x: 0, y: 100"], "The centre of the Stage is x: 0 and y: 0."),
    ("What does the X position control?", "Left and right", ["Up and down", "Size", "Volume"], "X controls left and right."),
    ("What does the Y position control?", "Up and down", ["Left and right", "Size", "Volume"], "Y controls up and down."),
    ("A sprite is on the left side of the Stage. Is its X positive or negative?", "Negative", ["Positive", "Zero", "It depends on the costume"], "Left of the centre means a negative X. Right of the centre means a positive X."),
    ("A sprite is below the centre of the Stage. Is its Y positive or negative?", "Negative", ["Positive", "Zero", "It depends on the sound"], "Below the centre means a negative Y. Above the centre means a positive Y."),
    ("What does the block set x to 100 do?", "Changes only X, moving the sprite sideways to x = 100", ["Changes both X and Y", "Changes only Y", "Moves the sprite 100 steps forward"], "set x to changes only X. set y to changes only Y."),
    ("What is the difference between go to x: y: and set x to?", "go to changes both X and Y, set x to changes only X", ["They are exactly the same", "go to changes only X, set x to changes both", "go to changes the costume"], "go to x: y: places the sprite at a full position. set x to only changes the sideways position."),
    ("Which block starts a program when the green flag is clicked?", "when green flag clicked", ["forever", "go to x: 0 y: 0", "play sound"], "when green flag clicked is an Events block and is usually the Start button."),
    ("What does the block change size by 10 do?", "Makes the sprite 10% bigger", ["Makes the sprite 10 steps bigger", "Sets the size to exactly 10%", "Makes the sprite smaller"], "change size by adds to the current size. A negative number makes the sprite smaller."),
    ("What does set size to 50% do?", "Makes the sprite smaller, at half its normal size", ["Makes the sprite bigger", "Hides the sprite", "Adds 50 to the size"], "set size to sets an exact size. 100% is normal size."),
    ("Which block makes a sprite talk for a short time and then stop?", "say Hello! for 2 seconds", ["say Hello!", "think Hmm...", "hide"], "say for seconds shows the words for a set time. Plain say keeps the words on the Stage."),
    ("What is the difference between start sound and play sound until done?", "play sound until done waits for the sound to finish before the next block runs", ["start sound is quieter", "They are exactly the same", "play sound until done cannot play music"], "start sound plays and moves on immediately. play sound until done waits."),
    ("What does the block change volume by -10 do?", "Makes the sound quieter", ["Makes the sound louder", "Stops all sounds", "Sets the volume to exactly 10%"], "A negative number lowers the volume. set volume to sets an exact volume."),
    ("What does a broadcast block do?", "Sends a message to other scripts", ["Plays a sound", "Changes the backdrop", "Makes a sprite bigger"], "A broadcast is like sending a message. The block that receives it is when I receive."),
    ("Which block receives a broadcast message?", "when I receive", ["when green flag clicked", "forever", "say"], "when I receive starts a script when the message arrives."),
    ("What does broadcast and wait do?", "Sends the message and waits for the receiving scripts to finish", ["Sends the message and continues at once", "Stops the project", "Waits for a key to be pressed"], "Plain broadcast continues immediately. broadcast and wait pauses until the receivers finish."),
    ("What does the forever block do?", "Repeats the blocks inside again and again, without stopping by itself", ["Repeats them 10 times", "Runs them once", "Waits one second"], "forever keeps going until the program is stopped."),
    ("Which Control block repeats actions a set number of times?", "repeat", ["forever", "wait", "stop all"], "repeat 10 runs the blocks inside ten times."),
    ("Which Control block lets a program make a decision?", "if then", ["repeat", "wait", "forever"], "if then runs its blocks only when the condition is true."),
    ("Which category do the touching blocks belong to?", "Sensing", ["Motion", "Sound", "Looks"], "Sensing blocks detect things like touching another sprite, the edge or the mouse."),
    ("What does the answer block hold, after ask and wait?", "What the player typed", ["The sprite's size", "The Stage's colour", "The volume"], "ask and wait shows a question, and answer contains what the player typed."),
    ("The AND operator is true when:", "Both conditions are true", ["Only one condition is true", "No condition is true", "The sprite is touching the edge"], "and needs both conditions. or needs at least one."),
    ("The OR operator is true when:", "At least one of the conditions is true", ["Both conditions are false", "Only when both are true", "The green flag is clicked"], "or is true if either condition (or both) is true."),
    ("What does the join block do?", "Puts words and numbers together", ["Adds two numbers", "Picks a random number", "Rounds a number"], "join hello and world makes helloworld. It is often used to build sentences."),
    ("What does the pick random block do?", "Chooses a random number between two numbers", ["Sorts numbers in order", "Rounds a number", "Adds two numbers"], "pick random 1 to 10 gives a number from 1 to 10 each time it runs."),
    ("What is a variable?", "A named place that stores information that can change, like a score", ["A type of sprite", "A backdrop", "A sound effect"], "Variables store information such as a score, lives or a level."),
    ("The score is 5. What is the score after change score by 1?", "6", ["1", "5", "0"], "change adds to the current value: 5 + 1 = 6. set score to 1 would make it exactly 1."),
    ("What is the difference between set and change for a variable?", "set gives an exact value, change adds to (or subtracts from) the current value", ["set adds and change gives an exact value", "They are exactly the same", "set hides the variable"], "set score to 0 resets the score. change score by 1 adds one point."),
    ("What are My Blocks?", "Blocks that you create yourself", ["Blocks that only work on the Stage", "Blocks that record sound", "Blocks made only by Scratch"], "My Blocks let you name a group of instructions and reuse it."),
    ("Why do we use My Blocks?", "To reuse code and keep big programs organised", ["To make the Stage bigger", "To change the backdrop", "To record your voice"], "One custom block can be used many times, so you do not rebuild the same blocks."),
    ("In a My Block, what is an input?", "A number or text you give the block when you use it", ["A sound file", "A costume", "A backdrop"], "An input lets one block work in different ways, for example move a different distance each time."),
]

INTERNET = [
    ("What is the Internet?", "A huge network that connects computers and other devices around the world", ["A program used to visit websites", "A company that sells phones", "One very large computer"], "The Internet is a huge network connecting devices around the world."),
    ("Which of these can connect to the Internet?", "A smart TV", ["A paper book", "A pencil", "A ruler"], "Laptops, phones, tablets, game consoles, smart TVs and smartwatches can all connect."),
    ("What is the difference between the Internet and Wi-Fi?", "The Internet is the worldwide network; Wi-Fi is a way to connect to a network without a cable", ["They are exactly the same thing", "Wi-Fi is a search engine", "The Internet is a type of cable"], "These two words are often confused. Wi-Fi is only one way of reaching the Internet."),
    ("What is a network?", "A group of connected devices", ["A single website", "A type of browser", "A kind of password"], "The Internet is a very large network of networks."),
    ("What is a website?", "A collection of related web pages available on the Internet", ["One single page", "A program for visiting websites", "A device that connects to Wi-Fi"], "For example, a school website may have Home, Courses, Teachers and Contact pages."),
    ("What is a web page?", "One page that you can view in a web browser", ["A whole collection of websites", "A company that gives Internet access", "A type of cable"], "A website is made of many web pages."),
    ("What is a web browser?", "A program used to access websites", ["A company that gives Internet access", "A device that connects to Wi-Fi", "A website that stores emails"], "Chrome, Firefox, Safari and Edge are browsers."),
    ("Which of these is a web browser?", "Mozilla Firefox", ["Bing", "DuckDuckGo", "Google Search"], "Firefox is a browser. Bing, DuckDuckGo and Google are search engines."),
    ("What does a search engine do?", "Helps you find information on the Internet", ["Connects your phone to Wi-Fi", "Stores your files", "Sends emails"], "You type what you want to find, for example weather in Kigali."),
    ("Which of these is a search engine?", "Bing", ["Safari", "Microsoft Edge", "Google Chrome"], "Bing is a search engine. Safari, Edge and Chrome are browsers."),
    ("Which sentence is correct?", "Chrome is a browser and Google is a search engine", ["Chrome is a search engine and Google is a browser", "Chrome and Google are both routers", "Chrome and Google are both websites you cannot open"], "You can open Google using Chrome."),
    ("What is a URL?", "The address of a page or resource on the Internet", ["A type of virus", "A kind of router", "A search engine"], "A URL tells the browser where to go, like a street address."),
    ("What is a link?", "Something you can click to go to another page or website", ["A cable between two computers", "A kind of password", "A type of email"], "Links can be text, images or buttons."),
    ("What is a server?", "A computer that provides information or services to other computers", ["A program for reading email", "A type of Wi-Fi", "A search engine"], "When you open a website your browser asks a server, and the server sends the page back."),
    ("What does ISP stand for?", "Internet Service Provider", ["Internet Safety Program", "International Search Page", "Internal Server Path"], "An ISP is a company that provides Internet access."),
    ("What is a router?", "A device that helps connect devices to a network", ["A program for browsing", "A website address", "A kind of email"], "A router is like a traffic controller that helps information reach the correct device."),
    ("What does a phone usually need to use mobile data?", "A SIM card or eSIM, a mobile network signal and a data plan", ["Only a Wi-Fi password", "An Ethernet cable", "A printer"], "Mobile data is provided through a mobile network."),
    ("You turn off Wi-Fi on your phone and browse using your SIM card. Which connection are you using?", "Mobile data", ["Wi-Fi", "Ethernet", "Bluetooth only"], "Using your SIM card means you are using mobile data."),
    ("Which type of connection uses a physical cable?", "Ethernet", ["Wi-Fi", "Mobile data", "Bluetooth"], "An Ethernet cable connects a device, such as a desktop computer, to a router."),
    ("Which of these is a risk of the Internet?", "Cyberbullying", ["Finding learning materials", "Communicating across countries", "Selling products online"], "Risks include scams, privacy problems, cyberbullying, false information and too much screen time."),
    ("Can we trust everything we read online?", "No, because anyone can publish information online", ["Yes, if it is on a website", "Yes, if it has pictures", "Yes, if it is long"], "Online information can be wrong, old, misleading or just an opinion."),
    ("Before believing information online, which question should you ask?", "Who wrote it?", ["How many colours does the page have?", "How many links are on the page?", "Is the page very long?"], "Also ask when it was published, what evidence is provided, and whether another reliable source confirms it."),
    ("Why should you check when a web page was published?", "Information can become old and out of date", ["Newer pages always load faster", "Old pages are always false", "The date changes the address"], "Look for the publication or update date."),
    ("Why should you check more than one source?", "If reliable sources agree, you have stronger evidence", ["Because one website is never enough to open", "Because it uses more mobile data", "Because sources always disagree"], "Do not immediately assume that a single website is correct."),
    ("What is clickbait?", "Content designed mainly to make people click", ["A tool for catching viruses", "A kind of search engine", "A type of email"], "A dramatic title does not mean the information is true."),
    ("When using an online map, what should you NOT do?", "Share your home address publicly", ["Search for a school", "Look for a park", "Search for Kigali"], "Do not share your home address publicly."),
    ("What is email?", "A way of sending and receiving messages using the Internet", ["A kind of web browser", "A cable between computers", "A search engine"], "An email can contain text, pictures or documents."),
    ("Which of these is an email address?", "student@gmail.com", ["www.student.com", "student.gmail", "https://student"], "An email address looks like name@service.com."),
    ("What goes in the To field of an email?", "The email address of the person who should receive it", ["Your own password", "The name of your browser", "The size of the file"], "Check the address carefully, because a wrong address sends the message to the wrong person."),
    ("What is the Subject of an email for?", "It tells the receiver what the email is about", ["It is where you type the address", "It is where you attach files", "It is your password"], "A good subject is short and clear, for example My Internet Homework."),
    ("What happens if you type the wrong email address?", "Your message may go to the wrong person", ["The email fixes the address by itself", "The email is always deleted", "Nothing can go wrong"], "Always check the address before sending."),
    ("What is an email attachment?", "A file included with an email", ["A reply to an email", "The subject line", "A kind of password"], "Attachments can be Word documents, spreadsheets, pictures or PDFs."),
    ("What does Compose mean in Gmail?", "Creating a new email", ["Deleting an email", "Replying to an email", "Signing out"], "Click Compose and a new email window appears."),
    ("What is the email safety rule about passwords?", "Your password is a secret, not a message", ["Share your password with friends you trust", "Send your password to teachers by email", "Write your password on the class board"], "If someone asks for your password, stop and ask a trusted adult."),
    ("Google says you are too young to create an account. What should you do?", "Stop and ask your teacher or parent for help", ["Enter a different age", "Ask a friend to make one for you in secret", "Use a stranger's phone number"], "Never enter a false age just to create an account."),
    ("What is phishing?", "An attempt to trick you into giving away information or doing something unsafe", ["A way of downloading music", "A type of search engine", "A fast Internet connection"], "Phishing often uses fear or urgency."),
    ("Which is a warning sign of a suspicious email?", "It demands immediate action, such as clicking a link right now", ["It is polite and comes from your teacher", "It tells you today's homework", "It has your correct name"], "Other signs: strange links, requests for passwords, unexpected prizes, and messages pretending to be someone else."),
    ("You get an email saying you won 5,000 dollars if you enter your Gmail password. What should you do?", "Do not click or reply, and show it to a teacher or trusted adult", ["Enter your password quickly", "Reply with your phone number", "Forward it to all your friends"], "Never give away your password. Stop and show the message to a trusted adult."),
    ("You receive an unexpected attachment called Congratulations!!!.exe from someone you do not know. What should you do?", "Do not open it", ["Open it to see what it is", "Download it and share it", "Reply and ask them to send more"], "Do not open unexpected attachments."),
    ("What is a file?", "Information stored digitally", ["A kind of router", "A search engine", "A type of cable"], "Examples: homework.docx, picture.jpg, music.mp3, project.pdf."),
    ("What does download mean?", "Receiving information from the Internet and saving it to your device", ["Sending a file from your device to the Internet", "Deleting a file", "Turning off Wi-Fi"], "Downloaded files usually appear in your Downloads folder."),
    ("What does upload mean?", "Sending a file from your device to an online service", ["Saving a file from the Internet to your device", "Reading a web page", "Printing a document"], "Upload is the opposite direction of download."),
    ("A stranger tells you to download a file that asks you to turn off your computer's security. What should you do?", "Do not download it, and ask a trusted adult", ["Download it quickly", "Turn off security and then download it", "Share the file with friends"], "Never download unknown files simply because someone tells you to."),
    ("Online messages should be:", "Clear, polite, respectful and appropriate", ["Rude but short", "Written in capital letters only", "Sent to strangers"], "Remember that a real person is reading your message."),
    ("During an online meeting, what should you do when you are not speaking?", "Mute yourself", ["Interrupt others", "Make noises", "Share the meeting link publicly"], "Also listen, do not interrupt and use respectful language."),
    ("Which of these should you NOT share with strangers online?", "Your home address", ["Your favourite colour", "Your favourite animal", "Your favourite sport"], "Personal information includes your full name, home address, phone number, password, school details, location and private photographs."),
    ("Which password is the strongest?", "A mixture of small and capital letters, numbers and special characters", ["Your first name", "1234", "The word password"], "Use strong, unique passwords that are hard to guess."),
    ("Which of these should you never announce publicly online?", "I am home alone", ["I like football", "My favourite colour is blue", "I am learning to use Word"], "Think carefully before sharing where you are."),
    ("What is cyberbullying?", "Bullying that happens using digital technology", ["A kind of computer virus", "A fast Internet connection", "A game"], "It can involve insults, threats, rumours, or leaving someone out on purpose."),
    ("Someone is bullying you online. What should you do?", "Do not respond with more bullying, block or report them, and tell a trusted adult", ["Bully them back", "Delete your account and tell nobody", "Share your password with them"], "Also save evidence if appropriate."),
    ("What is Artificial Intelligence (AI)?", "Technology that allows computers to perform tasks that normally need human-like abilities", ["A type of Wi-Fi", "A website address", "A kind of cable"], "AI can understand language, recognise images, translate, answer questions and create text or images."),
    ("AI can make mistakes. What should you do with important information from an AI?", "Always check it", ["Always believe it", "Ignore all AI answers", "Send it to your friends without checking"], "AI can give wrong facts, invent information or sound confident while being wrong."),
    ("What is a prompt?", "The instruction or question you give to an AI", ["A virus", "A type of website", "A kind of password"], "A better prompt gives a clear instruction."),
    ("Which is the best prompt?", "Give me five interesting facts about lions for a 10-year-old", ["animals", "lions??", "tell"], "Clear prompts tell the AI what you want and who it is for."),
    ("Which of these should you never give an AI?", "Your password", ["A question about the sky", "A request to explain photosynthesis", "A request for quiz questions"], "Do not give an AI your password, private family information, private photographs, financial information or other people's private information."),
    ("An AI says the largest planet is Earth. What is the best thing to do?", "Check with reliable sources, because AI is a helper and not the only source of truth", ["Believe it because AI is always right", "Copy it into your homework", "Ask the AI to say it again and stop there"], "Jupiter is the largest planet in our Solar System."),
    ("Which is a good way to use AI for schoolwork?", "Ask it to explain a difficult idea or create quiz questions to practise", ["Copy its answers and say you wrote them yourself", "Ask it to do all your homework", "Share your password so it can log in for you"], "Use AI to learn, not to avoid learning."),
]

# Wrong answers rewritten so they are about as long as the right answer. Without this, "pick the longest
# answer" would pass most of the exam without learning anything.
BALANCED_WRONG = {
    # Internet and AI
    "What is the Internet?": ["A program used to visit websites and read pages", "A company that sells phones, tablets and computers", "One very large computer that stores every website"],
    "What is the difference between the Internet and Wi-Fi?": ["The Internet is a Wi-Fi router; Wi-Fi is a website you visit with a browser", "The Internet is a cable in your home; Wi-Fi is the company that sells it", "They are exactly the same thing, so either word can be used for either"],
    "What is a network?": ["A collection of related web pages", "A program used to open websites", "A secret word that protects your account"],
    "What is a website?": ["A program used to visit and view websites online", "A device that connects your phone to the Internet", "One single page that you can read in a browser"],
    "What is a web page?": ["A whole collection of websites on the Internet", "A company that provides Internet access to homes", "A cable that connects a computer to a router"],
    "What does a search engine do?": ["Connects your phone to a Wi-Fi network", "Stores all the files that you create online", "Sends and receives your email messages"],
    "What is a URL?": ["A program that finds information for you online", "A device that connects your home to the ISP", "A company that provides Internet access to schools"],
    "What is a link?": ["A cable that joins two computers in a network", "A secret word that protects your online account", "A message that you send to another person by email"],
    "What is a server?": ["A program that lets you visit websites and pages", "A device that connects your home to the ISP", "A company that sells phones and mobile data plans"],
    "What is a router?": ["A program that helps you find pages on the web", "A company that provides Internet access to homes", "A computer that stores websites for other people"],
    "What does a phone usually need to use mobile data?": ["Only a Wi-Fi password and a wireless router at home", "An Ethernet cable connected to a desktop computer", "A printer and a memory card for storing pictures"],
    "Can we trust everything we read online?": ["Yes, if the information is on a website page", "Yes, because computers never make any mistakes", "Yes, if the page has pictures and videos on it"],
    "Why should you check when a web page was published?": ["Newer pages always load much faster than old ones", "Old pages are always false and should be deleted", "The date changes the address of the page online"],
    "Why should you check more than one source?": ["Because one website is never able to open on its own", "Because using more sources saves your mobile data", "Because different sources always give different facts"],
    "What is clickbait?": ["A tool that protects your computer from viruses", "A search engine that finds pictures and videos", "A type of email that comes from a teacher"],
    "When using an online map, what should you NOT do?": ["Search for a school near your home town", "Look for a park or a hospital in the area", "Search for the city of Kigali in Rwanda"],
    "What is email?": ["A web browser used to open websites and pages", "A cable that connects two computers together", "A search engine that finds information for you"],
    "What goes in the To field of an email?": ["The name of the browser that you are using", "The size of the file that you are attaching", "The password that protects your email account"],
    "What is the Subject of an email for?": ["It is where you type the address of the sender", "It is where you attach a picture or document", "It is where you write the password for the account"],
    "What is an email attachment?": ["A reply that you send to a message", "The short line that says what it is about", "A folder that keeps deleted messages"],
    "What is phishing?": ["A safe way of downloading music, videos and pictures from a website", "A special search engine used by teachers to find lesson plans", "A very fast Internet connection that is provided by an ISP company"],
    "Which is a warning sign of a suspicious email?": ["It is polite and comes from your teacher, who you know well", "It tells you about today's homework on the school platform", "It uses your correct name and the correct school address"],
    "You get an email saying you won 5,000 dollars if you enter your Gmail password. What should you do?": ["Enter your password quickly so that you get the prize", "Reply with your phone number so that they can call you", "Forward it to all your friends so that they win too"],
    "What is a file?": ["A device that connects to Wi-Fi", "A program that finds web pages", "A cable that joins two computers"],
    "What does download mean?": ["Sending a file from your device to an online service", "Deleting a file that you no longer need on your computer", "Turning off the Wi-Fi on your phone or tablet"],
    "What does upload mean?": ["Receiving a file from the Internet and saving it on your device", "Reading a web page in your browser window", "Printing a document on the school printer"],
    "A stranger tells you to download a file that asks you to turn off your computer's security. What should you do?": ["Download it quickly before the link stops working", "Turn off security and then download it anyway", "Share the file with friends so they can try it"],
    "Online messages should be:": ["Rude but short, so that people notice them", "Written in capital letters so they look important", "Sent to strangers so that you make more friends"],
    "Which password is the strongest?": ["Your first name written with a capital letter at the start", "The numbers 1234 because they are easy to remember", "The word password followed by your birth year"],
    "What is cyberbullying?": ["A kind of virus that spreads between computers", "A very fast Internet connection at home or school", "A type of game that people play with friends online"],
    "Someone is bullying you online. What should you do?": ["Bully them back so that they learn how it feels to be hurt", "Delete your account and do not tell any adult about it", "Share your password with them so that they stop the messages"],
    "What is Artificial Intelligence (AI)?": ["A special type of Wi-Fi network that works faster than a normal connection", "A kind of website address that ends with the letters AI in the URL", "A type of cable that connects a computer to a router in the home"],
    "What is a prompt?": ["A virus that spreads between computers", "A type of website that shows pictures", "A kind of password that protects your account"],
    "Which is the best prompt?": ["Tell me some things about animals in general", "Lions lions lions lions lions lions", "Write my whole lion homework so I can copy it"],
    "An AI says the largest planet is Earth. What is the best thing to do?": ["Believe it, because AI is always right about every single fact that it gives", "Copy it straight into your homework, because it sounds so confident and sure", "Ask the AI to say it again and then stop checking, because it repeated it"],
    "Which is a good way to use AI for schoolwork?": ["Copy its answers word for word and say that you wrote them yourself", "Ask it to do all of your homework so that you do not have to learn", "Share your password with it so that it can log in to your accounts"],
    # Scratch
    "What is Scratch?": ["A web browser that is used to open websites", "A spreadsheet program that adds up numbers", "A photo editor that changes colours in pictures"],
    "What is a sprite?": ["The background picture behind the Stage", "A sound that plays when you press a key", "A colour that you can add to a block"],
    "What is a costume?": ["The background picture of the Stage", "A programming block that plays a sound", "A place where the blocks are stored"],
    "What does the block set x to 100 do?": ["Changes both X and Y, moving the sprite to the corner", "Changes only Y, moving the sprite up to y = 100", "Moves the sprite 100 steps in the direction it faces"],
    "What is the difference between go to x: y: and set x to?": ["They are exactly the same, so you can use either one", "go to changes only X, and set x to changes both X and Y", "go to changes the costume, and set x to changes the size"],
    "What does set size to 50% do?": ["Makes the sprite bigger, at twice its normal size", "Hides the sprite so that nobody can see it", "Adds 50 to the sprite's current size each time"],
    "Which block makes a sprite talk for a short time and then stop?": ["say Hello! and keep it on the screen", "think Hmm... and hide the sprite", "hide the sprite for 2 seconds"],
    "What is the difference between start sound and play sound until done?": ["start sound is always quieter than play sound until done is", "They are exactly the same block, only with two different names", "play sound until done cannot be used to play music or sounds"],
    "What does a broadcast block do?": ["Plays a sound for the sprite to hear", "Changes the backdrop of the whole Stage", "Makes the sprite grow bigger and bigger"],
    "What does broadcast and wait do?": ["Sends the message and continues at once without waiting", "Stops the whole project until a key is pressed", "Waits for the player to type an answer to a question"],
    "What does the forever block do?": ["Repeats the blocks inside exactly ten times, then stops", "Runs the blocks inside only once, then stops the script", "Waits for one second, then plays a sound from the library"],
    "The OR operator is true when:": ["Both of the conditions are false at the same time", "Only when both of the conditions are true", "The green flag is clicked at the start of the game"],
    "What does the join block do?": ["Adds two numbers and shows the total", "Picks a random number between two others", "Rounds a number to the nearest whole number"],
    "What does the pick random block do?": ["Sorts a list of numbers from small to big", "Rounds a number to the nearest whole number", "Adds two numbers together and shows the total"],
    "What is a variable?": ["A type of sprite that can move around the Stage", "A picture that is used as a background on the Stage", "A sound effect that plays when the score changes"],
    "What is the difference between set and change for a variable?": ["set adds a number to the value and change gives an exact value", "They are exactly the same block with two different names", "set hides the variable from the Stage and change shows it again"],
    "Why do we use My Blocks?": ["To make the Stage bigger so that more sprites fit", "To change the backdrop of the game automatically", "To record your voice and save it as a new sound"],
    "In a My Block, what is an input?": ["A sound file that you record with a microphone", "A costume that you draw in the paint editor", "A backdrop that you choose for the Stage screen"],
    # Excel
    "What is Microsoft Excel mainly used for?": ["Writing long letters and printing them for school only", "Drawing pictures and editing photographs and videos only", "Browsing the internet and sending emails to friends only"],
    "A row in Excel goes:": ["From top to bottom of the sheet", "Diagonally from corner to corner", "Only in column A of the sheet"],
    "What is the Ribbon?": ["A single box where a row meets a column", "A picture of numbers such as a column chart", "The name that is written on each worksheet tab"],
    "What does the COUNT function do?": ["Adds all of the numbers in the cells together", "Finds the average of the numbers in the cells", "Finds the smallest number in a group of cells"],
    "What does Cut and Paste do?": ["Makes a copy and leaves the original in place", "Deletes the information and cannot bring it back", "Changes the font and the colour of the words"],
    "What does Conditional Formatting do?": ["Adds up all the numbers in the selected cells", "Sorts the names in a list from A to Z", "Inserts a picture from the computer into a cell"],
    "Merge & Center is used to:": ["Add up the numbers in two cells next to each other", "Delete a column that you do not need any more", "Copy a whole table to another place in the sheet"],
    "What does Wrap Text do?": ["Adds a border around the edge of the cell", "Changes the colour of the text in the cell", "Merges the cell with the cell below it"],
    "What is a chart for?": ["Adding up numbers automatically in a new column", "Correcting the spelling mistakes in a worksheet", "Saving the workbook to the Documents folder"],
    "You filter the Class column and choose P5. What happens?": ["All of the P5 students are deleted from the list", "The names are sorted from A to Z in the list", "The Class column is removed from the table"],
    "What does Sort A to Z do to a list of names?": ["Deletes the repeated names from the list", "Colours the names in a different colour", "Counts how many names are in the list"],
    "What does a hyperlink do?": ["Adds two numbers together in a new cell", "Draws a shape on the worksheet for you", "Changes the height of a row in the sheet"],
    "What is SmartArt used for?": ["Adding up numbers in a column quickly", "Sorting a list of data by the marks", "Finding and replacing words in a sheet"],
    "What does Format Painter do?": ["Adds up the numbers in a group of cells", "Sorts a list of names from A to Z", "Inserts a picture from the computer"],
}

BANKS = {
    "word": ("Microsoft Word final exam", WORD),
    "excel": ("Microsoft Excel final exam", EXCEL),
    "internet": ("Internet and AI final exam", INTERNET),
    "scratch": ("Scratch Programming final exam", SCRATCH),
}


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(2026)
    for slug, (title, bank) in BANKS.items():
        questions = []
        longest = 0
        for text, correct, wrong, why in bank:
            wrong = BALANCED_WRONG.get(text, wrong)
            assert len(wrong) == 3 and correct not in wrong, text
            longest += len(correct) > max(len(w) for w in wrong)
            options = [correct] + wrong
            rng.shuffle(options)
            # `why` documents the answer for teachers reviewing this file; learners are never shown it.
            questions.append({"text": text, "options": options, "correct": options.index(correct)})
        share = longest / len(bank)
        print(f"  correct answer is strictly the longest option in {round(100 * share)}% of questions")
        assert share <= 0.45, f"{slug}: answer-length bias too high; balance the wrong options"
        data = {
            "course": slug, "title": title, "pass_percent": 70, "questions_per_attempt": 20,
            "time_limit_minutes": 30, "retake_wait_minutes": 0, "questions": questions,
        }
        (OUT / f"{slug}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(slug, len(questions), "questions")


def export_for_docs():
    """Write tools/exam_docs_data.json (questions + explanations) for make_exam_docs.js."""
    out = {}
    for slug, (title, bank) in BANKS.items():
        data = json.loads((OUT / f"{slug}.json").read_text(encoding="utf-8"))
        why = {q[0]: q[3] for q in bank}
        out[slug] = {
            "title": title, "pass_percent": data["pass_percent"], "per_attempt": data["questions_per_attempt"],
            "minutes": data["time_limit_minutes"],
            "questions": [{"text": q["text"], "options": q["options"], "correct": q["correct"], "why": why[q["text"]]} for q in data["questions"]],
        }
    (Path(__file__).parent / "exam_docs_data.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    import sys

    build()
    if "--docs" in sys.argv:
        export_for_docs()
