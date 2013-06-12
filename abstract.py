import pygame.image
import pygame.rect
import os.path
from general import SolSet

def loadImage(name) :
	image =  pygame.image.load(os.path.join(SolSet.image_path, name + SolSet.image_type))
	return image.convert_alpha()


#Basic class on which all the other classes will depend
class AbstractObject(object) :
	def __init__(self, name, pos) :
		#Name of the object
		self.name = name
		#It's position and area (starts of as a 0 dimensional rect)
		self.rect = pygame.Rect(pos[0], pos[1], 0, 0) 

	#Checks if a x, y position is in the object
	def hasPosition(self, pos) :
		if not self.visible : return False
		return self.rect.collidepoint(pos)

	def hasCollision(self, obj) :
		return self.rect.colliderect(obj.rect)

	#Just returns the x, y position of self.rect
	def getPosition(self) :
		return (self.rect.x, self.rect.y)

	#Moving objects might not be as easy as chaing rect.x, so use subclass this if necessary
	def setPosition(self, pos) :
		self.rect.x, self.rect.y = pos[0], pos[1]

	def movePosition(self, move) :
		self.rect.move_ip(move)


#An object that has an image associated with it
#Can be made invisible
class AbstractImage(AbstractObject) :
	def __init__(self, name, pos, image) :
		AbstractObject.__init__(self, name, pos)
		#All objects have an image (surface) associated with them.
		self.image = self.setImage(image) 
		#Will this object be drawn (allows me to easily hide objects, rather than move rect off-screen)
		self.visible = True

	#The simple draw function that needs subclassed to be usefull
	def draw(self, screen) :
		if self.visible :
			screen.blit(image, self.rect)

	#Each object is associated with an image. As soon as the image is loaded, the self.rect attribute needs to be updated
	def setImage(self, image) :
		loaded = loadImage(image)
		self.rect.w, self.rect.h = loaded.get_width(), loaded.get_height()
		return loaded


#The basic container for cards. Subsequent piles will subclass it 
#The image represents the empty pile
class AbstractPile(AbstractImage) :

	def __init__(self, name, pos, image, cards = []) :
		AbstractImage.__init__(self, name, pos, image)
		self.cards = []
		self.addCards(cards)

	#Are there any cards in the pile?
	def isEmpty(self) : 
		if self.cards : return False
		return True

	#How many cards are in the pile
	def cardNum(self) : return len(self.cards)

	#Turns all the cards in the pile faceup or facedown
	def allFaceUp(self, boolean) :
		for card in self.cards :
			card.faceUp = boolean

	#Draws the bottom symbol stored in self.image (generally used to show an empty pile)
	def drawBottom(self, screen) :
		screen.blit(self.image, self.rect)

	#Remove cards from the top of the pile (end of the list)
	def takeCards(self, num) :
		 if num > self.cardNum() or num < 0 : raise IndexError
		 break_point = self.cardNum() - num
		 to_take = self.cards[break_point : ] #Cards that are taken
		 self.cards = self.cards [ : break_point] #Cards that remain
		 return to_take

	def takeAll(self) :
		return self.takeCards(self.cardNum())

	#The setPosition function moves all the cards, rather than setting the position directly
	#This allows tiled piles to be set correctly, as using setPosition directly would make the tiled pile into simple pile 
	def setPosition(self, pos) :
		x_move = pos[0] - self.rect.x
		y_move = pos[1] - self.rect.y

		super(AbstractPile, self).setPosition(pos)
		for card in self.cards : card.movePosition((x_move, y_move))

	def movePosition(self, move) :
		super(AbstractPile, self).movePosition(move)
		for card in self.cards : card.movePosition(move)

	#Simple function that takes cards and puts them back
	def returnCards(self, cards) :
		self.addCards(cards)

	#The rest of the functions need to be subclassed
	#Add a list of cards to the end of this pile. This is used to populate the pile originally
	def addCards(self, cards) :
		raise NotImplementedError

	def draw(self, screen) :
		raise NotImplementedError


#This is the abstract class for a pile where all the cards are exactly on top of each other
#It is fully functional if you want to just display this pile, but cannot be interacted with by user
class AbstractSimplePile(AbstractPile) :
	def __init__(self, name, pos, image, cards = []) :
		AbstractPile.__init__(self, name, pos, image, cards)

	#The draw call does not draw all the cards in the pile
	#Only the top card is drawn, as it hides all the other cards
	def draw(self, screen) :
		if not self.visible : return

		if  self.isEmpty():
			self.drawBottom(screen)

		else :
			self.cards[-1].draw(screen)

	#Can a cards be added to this pile by the user (for this class, always no)
	def validAddCards(self, pile) :
		return False

	#Add a single card (the card keeps track of where it was last added)
	def addSingle(self, card) :
		card.setPosition((self.rect.x, self.rect.y))
		card.pile = self
		self.cards.append(card)

	#Add cards to this pile
	#If you just want to know if cards could be added by user, run validAddPile
	def addCards(self, cards) :
		for card in cards : self.addSingle(card)


#The cards are now spread out vertically (with the last card in the list at the top)
#The tile pile has two spacings between cards
#init_space for the spacing when the pile is just created and add_space for the spacing when new cards are added
class AbstractTilePile(AbstractPile) :
	def __init__(self, name, pos, image, init_space, add_space, cards = []) :
		self.init_space = init_space
		self.add_space = add_space
		AbstractPile.__init__(self, name, pos, image, cards)

	def draw(self, screen) :
		if not self.visible : return
		if self.isEmpty(): self.drawBottom(screen)
		for card in self.cards : card.draw(screen)

	#Can a cards be added to this pile by the user (for this class, always no)
	def validAddCards(self, pile) :
		return False

	#This function is a little strained as it has to determine if a card is being added by the user
	#Or if cards are being returned to a pristine tiled pile
	#This is to ensure that the tile spacing does arbitarily switch
	def addSingle(self, card) :
		if self.isEmpty() :
			card.setPosition((self.rect.x, self.rect.y))
		else :
			last_card = self.cards[-1]
			#If the last card is faceUp, add the card with add_space spacing
			if last_card.faceUp : card.setPosition((last_card.rect.x, last_card.rect.y + self.add_space))
			#If the last card is faceDown, it means the card should be added with the init_space
			else : card.setPosition((last_card.rect.x, last_card.rect.y + self.init_space))

		card.pile = self
		self.cards.append(card)
		self.updateArea() #Don't forget to update the new area

	#Add cards to this pile
	#If you just want to know if cards could be added by user, run validAddPile
	def addCards(self, cards) :
		for card in cards : self.addSingle(card)

	#The rect area actually gets bigger as more cards are added, so it needs to be updated
	def updateArea(self) :
		if self.isEmpty() : 
			ref = self.image.get_rect()
			self.rect.h= ref.h

		else : #The hight of the tiled pile is simply the difference between the top of first and bottom of last card
			bottom = self.cards[-1].rect.bottom
			top = self.cards[0].rect.top
			self.rect.h = bottom - top

	#Remove cards from the top of the pile (end of the list)
	#Had to be subclassed to ensure the area is correctly updated
	def takeCards(self, num) :
		result = super(AbstractTilePile, self).takeCards(num)
		self.updateArea()
		return result

#A abstract class that can hold multiple piles if those piles need to talk to each other
#It does not have an image by itself, so self.rect has no dimension
#Which means that hasPosition has to be subclassed to allow user interaction and define pile interactions
class AbstractMultiPile(AbstractObject) :
	def __init__(self, name, pos, space) :
		AbstractObject.__init__(self, name, pos)
		self.space = space
		self.piles = []

	#Each added pile is spaced by self.space from the previous pile
	def setupPile(self, new_pile) :
		displace = 0
		for pile in self.piles :
			displace += pile.rect.width + self.space 
		new_pile.setPosition((self.rect.x + displace, self.rect.y))
		self.piles.append(new_pile)

	#Is a pile located at that position (return None if there is nothing)
	def getPile(self, pos) :
		for pile in self.piles :
			if pile.hasPosition(pos) : return pile

	def hasPosition(self, pos) :
		if self.getPile(pos) : return True
		return False

	def movePosition(self, move) :
		for pile in self.piles :
			pile.movePosition(move)

	def draw(self, screen) :
		for pile in self.piles :
			pile.draw(screen)