import pygame
import sys
from objects import *
from general import SolSet
from pygame.locals import *
import random

class DoubleClick :
	def __init__(self) :
		self.double_click = pygame.time.Clock()
		self.time = 0 #Necessary to temporary store time passed after checking second down click
		self.first_click = True #Is this the first click in the double click
		self.wasDC = False #Was the alst call to isDC() a double click

	#Implementing double click was a lot harder than initially thought
	#A double click starts on a mouse down and ends on the second mouse up
	#If there is too much time between the first and second mouse down, the second mouse down will be treated as a first
	def isDC(self, event) :
		if event.type == MOUSEBUTTONDOWN and event.button == 1 :
			click_time = self.double_click.tick() #Check how long since last click
			if not self.first_click : #If it's the first click, exit function with False
				#If it's the second downclick, make sure that a double click is still a possibility 
				#If not, make this down click the first click
				#Since tick() was called, store time passed in self.time, to be added to the upclick later
				if click_time > SolSet.double_speed : self.first_click = True
				else : self.time = click_time

		if event.type == MOUSEBUTTONUP and event.button == 1 :
			if not self.first_click : #If it's the second click
				click_time = self.double_click.tick() #Get time since last click (the second down click)
				self.first_click = True #The next click will again be first
				if click_time + self.time < SolSet.double_speed : #Add the click_time and self.time and check if fast enough
					self.wasDC = True 
					return True
			else : self.first_click = False #If it was first first upclick, now the second_click is expected
		#If we get to here, no double click was detected	
		self.wasDC = False
		return False


class Game :
	def __init__(self) :
		pygame.init()
		random.seed()

		self.screen = self.setDisplay() #Display dimensions
		self.double_click = DoubleClick() #Double click checker
		self.move_pile = Repository('Repository') #For moving piles

		self.cards = self.loadCards() #All the cards
		self.piles = self.populatePiles() #All the piles

	#The display dimensions are calculated given the wanted margins and card dimensions
	def setDisplay(self) :
		x_dim = (SolSet.margin_space * 2) + (SolSet.image_resolution[0] * 7) + (SolSet.start_space * 6)
		y_dim = SolSet.margin_space + (SolSet.image_resolution[1] * 2) + SolSet.row_space
		y_dim += (SolSet.tile_small_space * 6) + (SolSet.tile_large_space * 12)
		return pygame.display.set_mode((x_dim, y_dim))

	#Load the cards (the common card back and the card images)
	def loadCards(self) :
		Card.loadBack(SolSet.image_back)
		cards = [Card(x, (0, 0)) for x in SolSet.image_names]
		random.shuffle(cards)
		return cards

	#Place the piles (are reset the SuitPile win number down to 0)
	def populatePiles(self) :
		piles = []
		suit_piles = []
		SuitPile.total_cards = 0

		marker = 0 #Keeps track of the last card added
		x = SolSet.margin_space #The x_position of the pile
		y = SolSet.margin_space + SolSet.image_resolution[1] + SolSet.row_space
		for i in range(1,8) : #Need seven main piles
			pile_name = 'Main' + str(i)
			cards = self.cards[marker : i + marker] #Each pile position also tells me how many cards it needs
			piles.append(MainPile(pile_name, (x, y), SolSet.image_bottom, SolSet.tile_small_space, SolSet.tile_large_space, cards))

			#The suit piles are exactly above main piles (starting on the four one)
			if i > 3 : suit_piles.append(SuitPile('Suit' + str(i - 3), (x, SolSet.margin_space), SolSet.image_bottom))

			#tick along x and marker
			x += piles[-1].rect.w + SolSet.start_space
			marker = i + marker

		#Add the start pile 
		cards = self.cards[marker : 52] #The remaining cards
		piles.append(StartPile('Start', (SolSet.margin_space, SolSet.margin_space), SolSet.start_space, SolSet.image_bottom, cards))
		
		piles.extend(suit_piles) #The last four piles always must be the suit piles
		return piles

	#simply gets the pile that was clicked (none if no pile was clicked)
	def clickedPile(self, event) :
		for pile in self.piles :
			if pile.hasPosition(event.pos) : return pile

	#The basic idea of the game loop is thus :
	#If a pile is clicked, onClick() is run
	#If onClick() returns cards, this means that these cards can be moved around (while mouse is held down)
	#The moving of cards is performed by self.move_pile
	#With a double click, the down, up, and and click are read as single clicks (and still run as such)
	#The lst up click will result in onDoubleClick being called 
	def gameLoop(self) :
		while True :
			if self.winCondition() : 
				self.browninanMotion(2) #Move the piles around randomly if game has been won

	 		for event in pygame.event.get() :
	 			#Check and store if a double click occured
	 			if (event.type == MOUSEBUTTONUP or event.type == MOUSEBUTTONDOWN) and event.button == 1 :
					self.double_click.isDC(event)

				#Check if the program is quit
				if event.type == QUIT :
					pygame.quit()
					sys.exit()	

				#Pressing r resets the program
				if event.type == KEYUP and event.key == K_r :
					self.reset()

				#If the game has been won, reset it with a mouse click
				if self.winCondition():
					if event.type == MOUSEBUTTONUP and event.button == 1 :
						self.reset()

				#Now for the main meat of the program
				else :
					if event.type == MOUSEBUTTONUP and event.button == 1 :
						#Is the user currently dragging cards (and now wants to let them go)
						#I store it as the I need to check this variable again later and the cards might have been released
						move_pile_full = self.move_pile.hasCards() 

						if move_pile_full : #If yes
							#This finds the left most pile where the dropped cards are accepted
							selected_pile = None
							for pile in self.piles :
								if pile.validAddCards(self.move_pile.cards) : 
									selected_pile = pile
									break

							#If a valid pile is found, drop the cards there, otherwise return the cards
							if selected_pile : self.move_pile.addToPile(selected_pile)
							else : self.move_pile.returnCards()

						#The double click must come after the move_pile is resolved, so that no cards are even in the move_pile
						if self.double_click.wasDC : self.onDoubleClick(event)

						#If the move_pile was empty and no double click, just run a simple onClick on the pile
						if not move_pile_full and not self.double_click.wasDC :
						 	clicked_pile = self.clickedPile(event)

						 	if clicked_pile :
						 		clicked_pile.onClick(event)

					#If mouse is held down, move those cards to the self.move_pile
					if event.type == MOUSEBUTTONDOWN and event.button == 1 :
						clicked_pile = self.clickedPile(event)

					 	if clicked_pile :
					 		cards_taken = clicked_pile.onClick(event)
				 			if cards_taken : self.move_pile.addCards(cards_taken)

				 	#if the mouse is moved, move the mouse_pile (if it has cards)
				 	if event.type == MOUSEMOTION :
						if self.move_pile.hasCards() : self.move_pile.movePosition(event.rel)

			self.screen.fill((0, 0, 0))
			self.draw()
			pygame.display.flip()


	#When a double click occurs, try to put that card in the suit piles
	def onDoubleClick(self, event) :
		clicked_pile = self.clickedPile(event) #Get the clicked pile

		if clicked_pile :
			#onDoubleClick always returns only one card
			card_taken = clicked_pile.onDoubleClick(event)
			if card_taken : #If a card is returned (double click was valid)
				no_home = True #This card right now has no home in the Suit piles
				for pile in self.piles[-4:] : #Go through the four suit piles
					#The False ensures that the card_taken does not have to contact the Suit piles
					if pile.validAddCards(card_taken, False) : 
						pile.addCards(card_taken)
						no_home = False
						break;
				#If no suit pile has been found, return the card that was double clicked
				if no_home : card_taken[0].pile.addCards(card_taken)

	#Draw is simple, just draw all the piles
	def draw(self) :
		for pile in self.piles :
			pile.draw(self.screen)

		self.move_pile.draw(self.screen)

	def start(self) :
		self.gameLoop()

	#When all the cards are in the suit pile
	def winCondition(self) :
		return SuitPile.total_cards == len(self.cards)

	#Moves the piles randomly in all directions (the length arguement specifies how hard they move)
	def browninanMotion(self, length) :
		for pile in self.piles :
			x_move = random.randint(-length, length)
			y_move = random.randint(-length, length)
			pile.movePosition((x_move, y_move))

	def reset(self) :
	 	self.cards = self.loadCards()
		self.piles = self.populatePiles()

if __name__ == "__main__": 
	g = Game()
	g.start()