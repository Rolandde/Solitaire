import abstract
from pygame.locals import *

class Card(abstract.AbstractImage) :
	#The back of card image is stored here (it is the same for all cards)
	#Set if with self.loadBack()
	back_of_card = None

	#As static members are loaded before __main__ I cannot load the back_of_card image right away
	#This is because abstract.loadImage() calls a pygame function (convert_alpha) that requires pygame.init() to be called
	#This static function can be called to load the back_of_card image
	@staticmethod
	def loadBack(name) :
		Card.back_of_card = abstract.loadImage(name)

	#The two colors of the cards
	RED = 1
	BLACK = 2

	def __init__(self, name, pos) :
		#The name of the card is 01-13[cdhs]
		#Notice that the image for the card is specified by its name
		abstract.AbstractImage.__init__(self, name, pos, name)

		#Sometimes it is necessary to keep track of what pile a card is in
		self.pile = None

		self.faceUp = True

	def getNumber(self) : return int(self.name[:-1])

	def getSuit(self) : return self.name[-1]

	def getColor(self) :
		if self.getSuit() == 'h' or self.getSuit() == 'd' : return Card.RED
		return Card.BLACK

	def sameColor(self, card) :
		return self.getColor() == card.getColor()

	def draw(self, screen) :
		if self.visible :
			image = self.image if self.faceUp else Card.back_of_card
			screen.blit(image, self.rect)

#Encodes the draw and discard pile of the game
#The left draw pile if face down and upon click moves the top card onto the right discard pile faceup
#If the draw pile is empty, it takes all the cards from the discard pile
class StartPile(abstract.AbstractMultiPile) :
	DRAW = 0
	DISCARD = 1

	def __init__(self, name, pos, space, bottom, cards = []) :
		abstract.AbstractMultiPile.__init__(self, name, pos, space)
		self.setupPile(self.setupDraw(cards, bottom))
		self.setupPile(self.setupDiscard(bottom))

	#For the two setup functions, the position does not matter, as the setupPile function will correctly position the piles
	def setupDraw(self, cards, bottom) :
		draw_pile = abstract.AbstractSimplePile('Draw', (0,0), bottom, cards)
		draw_pile.allFaceUp(False)
		return draw_pile

	def setupDiscard(self, bottom) :
		discard_pile = abstract.AbstractSimplePile('Discard', (0,0), bottom)
		return discard_pile

	# If the draw pile is clicked 
	def drawUpClick(self) :
		if not self.piles[StartPile.DRAW].isEmpty() : 
			take_cards = self.piles[StartPile.DRAW].takeCards(1) #If the pile is not empty, get the top most card
			take_cards[0].faceUp = True
			self.piles[StartPile.DISCARD].addCards(take_cards) #Add the card to discard

		else : #Otherwise, move all the cards from discard to draw and but them facedowm
			self.piles[StartPile.DISCARD].allFaceUp(False)
			all_cards = self.piles[StartPile.DISCARD].takeAll()
			all_cards.reverse()
			self.piles[StartPile.DRAW].addCards(all_cards)

	#On click
	def onClick(self, event) :
		clicked_pile = self.getPile(event.pos)

		if not clicked_pile : return #Sanity check, just in case onClick was called accidentaly
		if not clicked_pile.visible: return

		if event.type == MOUSEBUTTONUP and event.button == 1 :
			if clicked_pile.name == 'Draw' : 
				self.drawUpClick()

		#Discard pile just returns the top card in a pile
		if event.type == MOUSEBUTTONDOWN and event.button == 1 :
			if clicked_pile.name == 'Discard' and not clicked_pile.isEmpty(): return clicked_pile.takeCards(1)

	#Double click is always MOUSEUP.
	#For the draw pile, does the same as single click
	#THe discard pile does not respond to single up clicks, but the double click takes the top card
	def onDoubleClick(self, event) :
		clicked_pile = self.getPile(event.pos)
		if not clicked_pile : return #Sanity check, just in case onClick was called accidentaly
		if not clicked_pile.visible: return

		if clicked_pile.name == 'Draw' : self.drawUpClick()
		if clicked_pile.name == 'Discard' and not clicked_pile.isEmpty() : return clicked_pile.takeCards(1)

	#Can cards be added to any of the piles
	def validAddCards(self, cards) :
		return False

	#I'm leaving this not implemented as there will never be a reason to call this function
	#I could just delete it, but this will remind me that it should not exist
	def addCards(self, cards) :
		raise NotImplementedError


#The 7 tiled piles that make up the main playing field
class MainPile(abstract.AbstractTilePile) :
	def __init__(self, name, pos, image, init_space, add_space, cards = []) :
		self.pileSetup(cards)
		abstract.AbstractTilePile.__init__(self, name, pos, image, init_space, add_space, cards)

	#All but the last card in the pile is facedown
	def pileSetup(self, cards) :
		for card in cards : card.faceUp = False
		if cards: cards[-1].faceUp = True

	#This function returns the top most card on the deck that was clicked
	#If no card was clicked, returns -1
	def topCardClicked(self, pos) :
		result = -1
		for i, card in enumerate(self.cards) :
			if card.hasPosition(pos) : result = i

		return result

	def onClick(self, event) :
		if not self.visible : return

		#When clicked down, return all the cards including and after the card clicked
		if event.type == MOUSEBUTTONDOWN and event.button == 1 :
			card_clicked = self.topCardClicked(event.pos)
			if card_clicked != -1 and self.cards[card_clicked].faceUp:
				cards_to_take = self.cardNum() - card_clicked
				return self.takeCards(cards_to_take)

		#If the last card in the pile if face down, an upclick will turn in around
		if event.type == MOUSEBUTTONUP and event.button == 1 :
			if not self.isEmpty() and self.cards[-1].hasPosition(event.pos) :
				self.cards[-1].faceUp = True

	#Returns the last card in the pile if it is faced up and has been clicked
	def onDoubleClick(self, event) :
		if not self.visible : return

		card_clicked = self.topCardClicked(event.pos)
		if card_clicked != -1 and self.cards[card_clicked].faceUp and card_clicked == self.cardNum() - 1:
			return self.takeCards(1)

	#can these cards be added to this pile by the user
	#We only care about the first card in cards
	#implicit assumption is that the rest of the program makes sure the order of the cards remains valid
	def validAddCards(self, cards) :
		#Only a king can be added to an empty pile
		if self.isEmpty() :
			if cards[0].getNumber() == 13 and self.hasCollision(cards[0]) : 
				return True
		else :
			ref_card = self.cards[-1] # The top most card of the pile determines validity
			if not ref_card.faceUp : #Card must be faceup to be seen when it is added to
				return False 

			if not ref_card.sameColor(cards[0]) and ref_card.getNumber() == cards[0].getNumber() + 1 :
				if ref_card.hasCollision(cards[0]) : 
					return True

		return False


#A simple pile that only allows addition of one card with increasing value with the same suit
#When empty, can accept only aces (the ace added will determine the suit)
#Keeps track of how many cards have been added to any SuitPile (for the win condition of 52)
class SuitPile(abstract.AbstractSimplePile) :
	total_cards = 0

	def __init__(self, name, pos, image) :
		abstract.AbstractSimplePile.__init__(self, name, pos, image)

	#validAddCards has to be expended
	#If contact is true, the added card must be in touch with the suit pile
	#This matters because double clicking a card can directly move it to a suit pile
	def validAddCards(self, cards, contact = True) :
		if contact : 
			if not self.hasCollision(cards[0]): return False
		if len(cards) != 1 : return False

		if self.isEmpty() :
			if cards[0].getNumber() == 1: return True
			return False

		ref_card = self.cards[-1]
		if ref_card.getSuit() == cards[0].getSuit() and ref_card.getNumber() + 1 == cards[0].getNumber() :
			return True
		return False

	#On click
	def onClick(self, event) :
		if not self.visible : return False

		if event.type == MOUSEBUTTONDOWN and event.button == 1 :
			if not self.isEmpty(): return self.takeCards(1)

	def onDoubleClick(self, event) :
		pass

	#To keep track of the total number of cards in SuitPiles, add and take card function need to be expanded
	def takeCards(self, num) :
		cards_taken = super(SuitPile, self).takeCards(num)
		SuitPile.total_cards -= num
		return cards_taken

	def addSingle(self, card) :
		super(SuitPile, self).addSingle(card)
		SuitPile.total_cards += 1
			
#This class allows for cards to be easily moved around
#It takes cards from a pile and keeps them in the same relative positions while they are moved around
#It also keeps track of where the cards came from and can return it if necessary
class Repository(object) :
	def __init__(self, name) :
		self.name = name
		self.cards = []
		self.source = None

	def addCards(self, cards) :
		if self.source or self.cards : raise Exception
		if cards :
			self.cards = cards
			self.source = cards[0].pile

	def hasCards(self) : 
		if self.cards : return True
		return False

	def clear(self) :
		self.cards = []
		self.source = None

	def returnCards(self) :
		self.source.addCards(self.cards)
		self.clear()

	#Move the card to the pile (please check if the move if valid first)
	def addToPile(self, pile) :
		pile.addCards(self.cards)
		self.clear()
 
	def draw(self, screen) :
		for card in self.cards : card.draw(screen)

	def movePosition(self, move) :
		for card in self.cards : card.movePosition(move)