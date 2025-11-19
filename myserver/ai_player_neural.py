#-----Imports-----
import asyncio
import websockets
import torch #Basically a matrix
from enum import Enum

#-----Creating chip class-----
#Each number represents the current state of a position
class Chip(Enum):
	EMPTY= [1,0,0]
	MINE= [0,1,0]
	THEIRS= [0,0,1]

def makeatensor(chip: Chip) -> torch.Tensor:
    return torch.tensor(chip.value, dtype=torch.float32)

#-----Storing the board as an array-----
#Creating a 2D array with empty chip objects
board = [[Chip.EMPTY for _ in range(7)] for _ in range(6)]

#-----AI go here-----
#Name of our AI: connect6x7
class AI(torch.nn.Module):
	def __init__(self, hidden_layers:int, hidden_size:int):
		super(AI, self).__init__()
        
        #42 input nodes, representing the possible 2D positions
		self.layers = torch.nn.Sequential(
			torch.nn.Linear(42, hidden_size),
			*[torch.nn.Linear(hidden_size,hidden_size), torch.nn.ReLU() for _ in range(hidden_layers)],
			
            #7 int outputs, representing the position of the columns
            torch.nn.Linear(hidden_size, 7),
		)


#-----Method to calculate the actual move the AI should make (The actual important stuff)-----
def calculate_move(currBoard:torch.Tensor)->int:
    #The AI will play against a PERFECT AI and will "learn" from it
    #BASED ON THE TRAINING, we want the AI to generally follow the instructions below
    #(also these comments are here for the paper part of the project so pls no delete)
    #https://www.rd.com/article/how-to-win-connect-4/
    
    """
    GOAL - Force player to make moves such that when it's the AI's turn, the AI has two possible
           winning positions at the same time which would then be impossible for the second player
           to block (ensuring a win)
    
    [From article]
    In Connect 4 parlance, whenever three playing pieces are lined up adjacently, it’s called a “major threat,”
    even if it might take several moves to complete the line-of-four (due to the vertical nature of the columns).
    An “adjacent threat pair” refers to two major threats that are connected by at least one playing piece. And
    forming an adjacent threat pair—also known as “forking your threats”—is one key to a quicker win than you may
    achieve using the parity strategy, says Galli.
    """

    #If the AI is the beginning player....
        #choose the 4th column [0][3]
		"""
        Also known as the parity strategy, “playing the odd rows” is when the first player 
        aims to secure three pieces in a line so that an empty fourth spot is in one of the 
        odd-numbered rows (the first, third or fifth from the bottom). That line can be horizontal, 
        vertical or diagonal. Galli says that this is not only his favorite how-to-win Connect 4 strategy
        but also the one that is talked about least on social media—thus making it all the more powerful
        for those in the know.

        Given the finite number of positions on the grid, and assuming perfect play, this strategy should
        have the effect of leaving one of the columns “either free or nearly free” by the 37th move of the
        game, Galli notes. This will have the effect of forcing the second player to place their piece in the
        last spot before the first player’s winning spot.
        """

    #If the AI is the second player....
        #Same goal as above
        """
        The parity strategy discussed above works for the second player as well, except that the second player
        must set up their three-in-line in an even row, Galli points out. Of course, while setting things up as
        such, “you still have to make sure you're not ignoring some other risk.” In other words, even as you play
        offensively, it’s still important to play defensively, eliminating any advantage gained by the first player
        in an earlier move. This, of course, applies to the odd-parity play as well.
        """

    #IN THE CASE OF "DEFENDING"
    """
    In Connect 4 parlance, whenever three playing pieces are lined up adjacently, it’s called a “major threat,”
    even if it might take several moves to complete the line-of-four (due to the vertical nature of the columns).
    An “adjacent threat pair” refers to two major threats that are connected by at least one playing piece. And
    forming an adjacent threat pair—also known as “forking your threats”—is one key to a quicker win than you may
    achieve using the parity strategy, says Galli.

    Galli’s preferred fork is known by many as the “figure 7 trap” because the player making use of it creates a
    seven-shaped formation of their playing pieces. This involves three pieces in a diagonal line, where the top
    piece is also part of a three-piece horizontal line. If executed in the center of the board, in any orientation,
    this offers multiple opportunities for a win, and that can be difficult, if not impossible, for the other player
    to block. As you play more, you’re likely to pick up on other forks as they arise organically, Allis notes.
    """


    
    

    
    
    
    #Output is an int representing the column to put circle thing
    #output = make a call to the ai network
    #Returning the output
    return output













#-----Sending information to and from the server-----
async def gameloop (socket, created):
	active = True
	while active: # While game is active, continually anticipate messages
		message = (await socket.recv()).split(':') # Receive message from server
		match message[0]:
			case 'GAMESTART': # Game has started
				if created: # If we created the game, it's our turn since we go first
					col = calculate_move(None) # calculate_move is some arbitrary function you have created to figure out the next move
					await socket.send(f'PLAY:{col}') # Send your move to the server

			case 'OPPONENT': # Opponent has gone; calculate next move
				col = calculate_move(message[1]) # Give your function your opponent's move
				await socket.send(f'PLAY:{col}') #  Send your move to the server

			case 'WIN' | 'LOSS' | 'DRAW' | 'TERMINATED': # Game has ended
				print(message[0])
				active = False

async def create_game (server):
	async with websockets.connect(f'ws://{server}/create') as socket: # Establish websocket connection
		await gameloop(socket, True)

async def join_game(server, id):
	async with websockets.connect(f'ws://{server}/join/{id}') as socket: # Establish websocket connection
		await gameloop(socket, False)

#-----Main-----
if __name__ == '__main__': # Program entrypoint
	server = input('Server IP: ').strip() # Get IP from console
	protocol = input('Join game or create game? (j/c): ').strip() # Get action from console

	match protocol:
		case 'c':
			asyncio.run(create_game(server))
		case 'j':
			id = input('Game ID: ').strip()
			asyncio.run(join_game(server, id))
		case _:
			print('Invalid protocol!')