import pygame
import sys
import cv2
import numpy as np
import random
import os
from hand_detector import HandDetector

# Initialize Pygame and OpenCV
pygame.init()
detector = HandDetector()

# Game window settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Hand Controlled Car Racing")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
CYAN = (0, 255, 255)

# Car properties
car_width = 40
car_height = 60
car_x = WINDOW_WIDTH // 2 - car_width // 2
car_y = WINDOW_HEIGHT - car_height - 20
car_speed = 5
initial_car_y = car_y  # Store initial position

# Obstacle and game properties
obstacles = []
obstacle_width = 60
obstacle_height = 60
score = 0
font = pygame.font.Font(None, 36)
game_over = False
high_score = 0
obstacle_count = 0  # Track total number of spawned obstacles
obstacles_per_spawn = 1  # Number of obstacles in a wave, increases over time
max_obstacles_per_spawn = 3  # Cap the number of obstacles in a wave

# Power-up properties
powerups = []
SHIELD_DURATION = 300  # 5 seconds at 60 FPS
shield_active = False
shield_timer = 0

# Difficulty settings
initial_obstacle_speed = 5
obstacle_speed = initial_obstacle_speed
max_obstacle_speed = 15
speed_increase_rate = 0.1
base_spawn_interval = 60  # Base interval for random spawn timing (frames)
min_spawn_interval = 20  # Minimum interval for random spawn timing

# Particle system
particles = []
PARTICLE_LIFETIME = 30
PARTICLE_COLORS = [(255, 165, 0), (255, 69, 0), (255, 0, 0)]  # Orange to red colors

# Background and lane properties
lane_width = 10
lane_height = 80
lane_gap = 20
num_lanes = 5
lanes = []
lane_positions = []
lane_speed = 5

# Initialize lanes and their positions
lane_spacing = WINDOW_WIDTH // (num_lanes + 1)
for i in range(1, num_lanes + 1):
    x_pos = i * lane_spacing
    lane_positions.append(x_pos)
    for y in range(-lane_height, WINDOW_HEIGHT + lane_height, lane_height + lane_gap):
        lanes.append({'x': x_pos, 'y': y})

# Calculate positions between lanes
between_lane_positions = []
# Add position before first lane (midpoint between x=0 and first lane)
between_lane_positions.append(lane_positions[0] // 2)
# Add midpoints between consecutive lanes
for i in range(len(lane_positions) - 1):
    midpoint = (lane_positions[i] + lane_positions[i + 1]) // 2
    between_lane_positions.append(midpoint)
# Add position after last lane (midpoint between last lane and WINDOW_WIDTH)
between_lane_positions.append((lane_positions[-1] + WINDOW_WIDTH) // 2)

# Spawn timers for staggered spawning
spawn_timers = []  # List of timers for each obstacle in the current wave
spawn_intervals = []  # Random intervals for each obstacle

# Load high score from file
def load_high_score():
    try:
        with open('high_score.txt', 'r') as f:
            return int(f.read().strip())
    except:
        return 0

# Save high score to file
def save_high_score(score):
    with open('high_score.txt', 'w') as f:
        f.write(str(score))

# Initialize high score
high_score = load_high_score()

# Load images
try:
    player_car_img = pygame.image.load('d:/vscode/new/game/resources/player_car.png')
    player_car_img = pygame.transform.scale(player_car_img, (car_width, car_height))
    
    # Load multiple obstacle car images
    obstacle_car_images = []
    resources_path = 'd:/vscode/new/game/resources'
    for file in os.listdir(resources_path):
        if file.startswith('obstacle') and file.endswith('.png'):
            img = pygame.image.load(os.path.join(resources_path, file))
            img = pygame.transform.rotate(img, 180)
            img = pygame.transform.scale(img, (obstacle_width, obstacle_height))
            obstacle_car_images.append(img)
except:
    player_car_img = None
    obstacle_car_images = []

# Initialize webcam
cap = cv2.VideoCapture(0)

# Game loop
clock = pygame.time.Clock()
running = True

def create_particles(x, y, amount=20):
    for _ in range(amount):
        angle = random.uniform(0, 2 * np.pi)
        speed = random.uniform(2, 5)
        size = random.randint(3, 6)
        lifetime = PARTICLE_LIFETIME
        color = random.choice(PARTICLE_COLORS)
        particles.append({
            'x': x,
            'y': y,
            'dx': speed * np.cos(angle),
            'dy': speed * np.sin(angle),
            'size': size,
            'lifetime': lifetime,
            'color': color
        })

def initialize_spawn_timers():
    """Initialize random spawn timers for the current wave."""
    global spawn_timers, spawn_intervals
    spawn_timers = []
    spawn_intervals = []
    # Adjust spawn interval based on score
    current_interval = max(min_spawn_interval, base_spawn_interval - score)
    for _ in range(obstacles_per_spawn):
        # Random interval between min_spawn_interval and current_interval
        interval = random.randint(min_spawn_interval, current_interval)
        spawn_timers.append(0)  # Start timer at 0
        spawn_intervals.append(interval)

# Initialize first wave
initialize_spawn_timers()

while running:
    # OpenCV hand detection
    success, img = cap.read()
    if not success:
        continue
    
    img = detector.find_hands(img)
    hand_position = detector.get_hand_position(img)
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break
        elif event.type == pygame.KEYDOWN and game_over:
            if event.key == pygame.K_SPACE:
                # Reset game
                game_over = False
                score = 0
                obstacles.clear()
                powerups.clear()
                car_x = WINDOW_WIDTH // 2 - car_width // 2
                car_y = WINDOW_HEIGHT - car_height - 20
                obstacle_speed = initial_obstacle_speed
                obstacle_count = 0
                obstacles_per_spawn = 1
                shield_active = False
                shield_timer = 0
                initialize_spawn_timers()

    # Update game state
    if not game_over:
        # Update car position
        if hand_position['center_x'] != 0:
            car_x = np.interp(hand_position['center_x'], [100, 540], [WINDOW_WIDTH - car_width, 0])
            car_y = np.interp(hand_position['center_y'], [100, 400], [initial_car_y, initial_car_y - 200])
        
        # Update shield timer
        if shield_active:
            shield_timer += 1
            if shield_timer >= SHIELD_DURATION:
                shield_active = False
                shield_timer = 0
        
        # Update spawn timers
        for i in range(len(spawn_timers)):
            spawn_timers[i] += 1
            if spawn_timers[i] >= spawn_intervals[i]:
                # Spawn an obstacle in a random between-lane position
                between_x = random.choice(between_lane_positions)
                new_obstacle = {
                    'x': between_x - obstacle_width//2,  # Center in between-lane position
                    'y': -obstacle_height,
                    'passed': False,
                    'image': random.choice(obstacle_car_images) if obstacle_car_images else None
                }
                obstacles.append(new_obstacle)
                obstacle_count += 1
                # Reset this timer with a new random interval
                spawn_timers[i] = 0
                current_interval = max(min_spawn_interval, base_spawn_interval - score)
                spawn_intervals[i] = random.randint(min_spawn_interval, current_interval)
                
                # Random chance to spawn power-up
                if random.random() < 0.05:  # 5% chance
                    powerup = {
                        'x': random.randint(0, WINDOW_WIDTH - 30),
                        'y': -30,
                        'type': 'shield',
                        'width': 30,
                        'height': 30
                    }
                    powerups.append(powerup)
                
                # Increase speed and number of obstacles every 3 spawns
                if obstacle_count % 3 == 0:
                    obstacle_speed = min(max_obstacle_speed, obstacle_speed + speed_increase_rate)
                    obstacles_per_spawn = min(max_obstacles_per_spawn, obstacles_per_spawn + 1)
                    # Add new timer if obstacles_per_spawn increased
                    if len(spawn_timers) < obstacles_per_spawn:
                        spawn_timers.append(0)
                        spawn_intervals.append(random.randint(min_spawn_interval, current_interval))

    # Update obstacles and power-ups
    for obstacle in obstacles[:]:
        obstacle['y'] += obstacle_speed
        
        # Check collision
        car_rect = pygame.Rect(car_x, car_y, car_width, car_height)
        obstacle_rect = pygame.Rect(obstacle['x'], obstacle['y'], obstacle_width, obstacle_height)
        
        if car_rect.colliderect(obstacle_rect) and not shield_active:
            create_particles(car_x + car_width//2, car_y + car_height//2)
            # Update high score before game over
            if score > high_score:
                high_score = score
                save_high_score(high_score)
            game_over = True
            break
        
        # Score update (only when not game over)
        if not game_over and obstacle['y'] > car_y + car_height and not obstacle.get('passed', False):
            score += 1
            obstacle['passed'] = True
        
        # Remove off-screen obstacles
        if obstacle['y'] > WINDOW_HEIGHT:
            obstacles.remove(obstacle)

    # Update power-ups
    for powerup in powerups[:]:
        powerup['y'] += obstacle_speed * 0.7  # Slower than obstacles
        
        # Check collection
        powerup_rect = pygame.Rect(powerup['x'], powerup['y'], powerup['width'], powerup['height'])
        if car_rect.colliderect(powerup_rect):
            if powerup['type'] == 'shield':
                shield_active = True
                shield_timer = 0
            powerups.remove(powerup)
            continue
        
        # Remove off-screen powerups
        if powerup['y'] > WINDOW_HEIGHT:
            powerups.remove(powerup)

    # Draw game elements
    screen.fill(GRAY)
    
    # Draw lanes
    for lane in lanes:
        lane['y'] += lane_speed
        if lane['y'] > WINDOW_HEIGHT:
            lane['y'] = -lane_height
        pygame.draw.rect(screen, YELLOW, (lane['x'], lane['y'], lane_width, lane_height))
    
    # Draw obstacles
    for obstacle in obstacles:
        if obstacle.get('image'):
            screen.blit(obstacle['image'], (obstacle['x'], obstacle['y']))
        else:
            pygame.draw.polygon(screen, WHITE, [
                (obstacle['x'], obstacle['y'] + obstacle_height),
                (obstacle['x'] + obstacle_width//2, obstacle['y']),
                (obstacle['x'] + obstacle_width, obstacle['y'] + obstacle_height)
            ])
    
    # Draw power-ups
    for powerup in powerups:
        pygame.draw.circle(screen, CYAN, 
                          (int(powerup['x'] + powerup['width']//2), 
                           int(powerup['y'] + powerup['height']//2)), 15)
    
    # Draw player car
    if player_car_img:
        screen.blit(player_car_img, (car_x, car_y))
    else:
        pygame.draw.polygon(screen, RED, [
            (car_x, car_y + car_height),
            (car_x + car_width//2, car_y),
            (car_x + car_width, car_y + car_height)
        ])
    
    # Draw shield effect
    if shield_active:
        pygame.draw.circle(screen, (0, 255, 255, 128), 
                          (int(car_x + car_width//2), 
                           int(car_y + car_height//2)), 
                          max(car_width, car_height), 2)
    
    # Update and draw particles
    for particle in particles[:]:
        particle['x'] += particle['dx']
        particle['y'] += particle['dy']
        particle['lifetime'] -= 1
        if particle['lifetime'] > 0:
            pygame.draw.circle(screen, particle['color'], 
                              (int(particle['x']), int(particle['y'])), particle['size'])
        else:
            particles.remove(particle)
    
    # Draw score
    score_text = font.render(f'Score: {score}', True, WHITE)
    screen.blit(score_text, (10, 10))
    
    # Draw game over screen with black popup
    if game_over:
        # Create a semi-transparent black popup
        popup_surface = pygame.Surface((400, 300), pygame.SRCALPHA)
        popup_surface.fill((0, 0, 0, 200))  # Black with 200/255 opacity
        popup_rect = popup_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
        
        # Render text
        game_over_text = font.render('Game Over!', True, WHITE)
        final_score_text = font.render(f'Final Score: {score}', True, WHITE)
        high_score_text = font.render(f'High Score: {high_score}', True, WHITE)
        restart_text = font.render('Press SPACE to restart', True, WHITE)
        
        # Calculate text positions
        text_y = popup_rect.top + 50
        text_spacing = 50
        
        # Blit text onto popup surface
        popup_surface.blit(game_over_text, 
                          (popup_rect.width//2 - game_over_text.get_width()//2, 30))
        popup_surface.blit(final_score_text, 
                          (popup_rect.width//2 - final_score_text.get_width()//2, 30 + text_spacing))
        popup_surface.blit(high_score_text, 
                          (popup_rect.width//2 - high_score_text.get_width()//2, 30 + 2*text_spacing))
        popup_surface.blit(restart_text, 
                          (popup_rect.width//2 - restart_text.get_width()//2, 30 + 3*text_spacing))
        
        # Draw popup on screen
        screen.blit(popup_surface, popup_rect)

    # Update display
    pygame.display.flip()
    clock.tick(60)
    
    # Show OpenCV window
    cv2.imshow("Hand Tracking", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
pygame.quit()
sys.exit()