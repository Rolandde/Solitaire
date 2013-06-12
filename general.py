def cardNames() :
	suits = ['d', 'h', 'c', 's']
	cards = []

	for card_num in range(1, 14) :
		for card_suit in suits :
			str_card = str(card_num) if card_num > 9 else '0' + str(card_num) 
			cards.append(str_card + card_suit)

	return cards

class SolSet :
	image_names = cardNames()
	image_path = 'cards'
	image_type = '.gif'
	image_back = 'back01'
	image_bottom = 'bottom02-n'
	image_resolution = (80, 122)
	start_space = 10
	row_space = 30
	margin_space = 20
	tile_small_space = 5
	tile_large_space = 15
	double_speed = 500