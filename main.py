DESTROYED_KEY = "__destroyed"
BALL_IMAGE = img("""
    . . e e 1 e e e . .
        . e 1 1 d d d d e .
        e 1 d d d d d d d e
        e d d d d d d d d e
        e d d d d d d d d e
        e d d d d d d d d e
        e d d d d d d d d e
        . e d d d d d d e .
        . . e e e e e e . .
""")
PADDLE_SPEED = 150
PADDING_FROM_WALL = 3
pingMessage = False
# if player doesn't interact for 'TIMEOUT' time, revert to ai
TIMEOUT = 5000
playerOneLastMove = -TIMEOUT
playerTwoLastMove = -TIMEOUT
controller.set_repeat_default(0, 1000)
controller.up.on_event(ControllerButtonEvent.REPEATED,
    lambda: playerOneLastMove = game.runtime())
controller.down.on_event(ControllerButtonEvent.REPEATED,
    lambda: playerOneLastMove = game.runtime())
controller.player2.up.on_event(ControllerButtonEvent.REPEATED,
    lambda: playerTwoLastMove = game.runtime())
controller.player2.down.on_event(ControllerButtonEvent.REPEATED,
    lambda: playerTwoLastMove = game.runtime())
playerOne = createPlayer(info.player1)
playerOne.left = PADDING_FROM_WALL
controller.move_sprite(playerOne, 0, PADDLE_SPEED)
playerTwo = createPlayer(info.player2)
playerTwo.right = screen.width - PADDING_FROM_WALL
controller.player2.move_sprite(playerTwo, 0, PADDLE_SPEED)
createBall()
def createPlayer(player: info.PlayerInfo):
    output = sprites.create(image.create(3, 18), SpriteKind.player)
    output.image.fill(player.bg)
    output.set_flag(SpriteFlag.STAY_IN_SCREEN, True)
    player.set_score(0)
    player.show_player = False
    return output
def createBall():
    ball = sprites.create(BALL_IMAGE.clone(), SpriteKind.enemy)
    ball.vy = randint(-20, 20)
    ball.vx = 60 * (1 if Math.percent_chance(50) else -1)
    
    # unknown expression:  178
    ball.data = {}
    

def on_on_update():
    
    def on_for_each(b):
        # tagged as destroyed
        if b.data[DESTROYED_KEY]:
            return
        scoreRight = b.x < 0
        scoreLeft = b.x >= screen.width
        if scoreRight:
            info.player2.change_score_by(1)
        elif scoreLeft:
            info.player1.change_score_by(1)
        if b.top < 0:
            b.vy = abs(b.vy)
        elif b.bottom > screen.height:
            b.vy = -abs(b.vy)
        if scoreLeft or scoreRight:
            b.destroy(effects.disintegrate, 500)
            b.data[DESTROYED_KEY] = True
            
            def on_run_in_parallel():
                pause(250)
                createBall()
            control.run_in_parallel(on_run_in_parallel)
            
    sprites.all_of_kind(SpriteKind.enemy).for_each(on_for_each)
    
game.on_update(on_on_update)

def on_on_shade():
    if pingMessage:
        screen.print_center("ping", 5)
    else:
        screen.print_center("pong", 5)
game.on_shade(on_on_shade)

def on_on_overlap(sprite, otherSprite):
    global pingMessage
    fromCenter = otherSprite.y - sprite.y
    otherSprite.vx = otherSprite.vx * -1.05
    otherSprite.vy += (sprite.vy >> 1) + (fromCenter * 3)
    otherSprite.start_effect(effects.ashes, 150)
    sprite.start_effect(effects.ashes, 100)
    otherSprite.image.set_pixel(randint(1, otherSprite.image.width - 2),
        randint(1, otherSprite.image.height - 2),
        sprite.image.get_pixel(0, 0))
    pingMessage = not pingMessage
    # time out this event so it doesn't retrigger on the same collision
    pause(500)
sprites.on_overlap(SpriteKind.player, SpriteKind.enemy, on_on_overlap)

controller.A.on_event(ControllerButtonEvent.PRESSED, lambda: addBall(info.player1))
controller.B.on_event(ControllerButtonEvent.PRESSED,
    lambda: removeBall(info.player1))
controller.player2.A.on_event(ControllerButtonEvent.PRESSED, lambda: addBall(info.player2))
controller.player2.B.on_event(ControllerButtonEvent.PRESSED,
    lambda: removeBall(info.player2))
def addBall(player: info.PlayerInfo):
    player.change_score_by(-2)
    createBall()
def removeBall(player: info.PlayerInfo):
    balls = sprites.all_of_kind(SpriteKind.enemy)
    if len(balls) > 1:
        Math.pick_random(balls).destroy()
        player.change_score_by(-2)

def on_on_update2():
    currTime = game.runtime()
    if playerOneLastMove + TIMEOUT < currTime:
        trackBall(playerOne)
    if playerTwoLastMove + TIMEOUT < currTime:
        trackBall(playerTwo)
    def trackBall(player: Sprite):
        next2 = nextBall(player)
        if ballFacingPlayer(player, next2):
            # move to where ball is expected to intersect
            intersectBall(player, next2)
        else:
            # relax, ball is going other way
            player.vy = 0
    def nextBall(player: Sprite):
        def on_sort(a, b):
            # if one of the balls is destroyed, ignore it
            if a.data:
                return 1
            elif b.data:
                return -1
            aFacingPlayer = ballFacingPlayer(player, a)
            bFacingPlayer = ballFacingPlayer(player, b)
            # else prefer ball facing player
            if aFacingPlayer and not bFacingPlayer:
                return -1
            elif not aFacingPlayer and bFacingPlayer:
                return 1
            # else prefer ball that will next reach player
            aDiff = abs((a.x - player.x) / a.vx)
            bDiff = abs((b.x - player.x) / b.vx)
            return aDiff - bDiff
        return sprites.all_of_kind(SpriteKind.enemy).sort(on_sort)[0]
    def ballFacingPlayer(player: Sprite, ball: Sprite):
        return (ball.vx < 0 and player.x < 80) or (ball.vx > 0 and player.x > 80)
    def intersectBall(player: Sprite, target: Sprite):
        global PADDLE_SPEED
        projectedDY = (target.x - player.x) * target.vy / target.vx
        intersectionPoint = target.y - projectedDY
        # quick 'estimation' for vertical bounces
        if intersectionPoint < 0:
            intersectionPoint = abs(intersectionPoint % screen.height)
        elif intersectionPoint > screen.height:
            intersectionPoint -= intersectionPoint % screen.height
        # move toward estimated intersection point if not in range
        if intersectionPoint > player.y + (player.height >> 2):
            player.vy = PADDLE_SPEED
        elif intersectionPoint < player.y - (player.height >> 2):
            player.vy = -PADDLE_SPEED
        else:
            player.vy = 0
game.on_update(on_on_update2)
