import pygame
import math
import sys

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 1000, 700
FPS = 60

# Colors
BG_COLOR = (25, 28, 36)
DRONE_BODY = (40, 40, 40)
DRONE_ARM = (180, 180, 180)
FPGA_COLOR = (45, 180, 100)
SIGNAL_TELEMETRY = (0, 200, 255)  # Cyan
SIGNAL_CMD = (255, 60, 60)        # Red
ALERT_COLOR = (255, 50, 50)
TEXT_COLOR = (255, 255, 255)

class Drone:
    def __init__(self, id, x, y, z=100.0):
        self.id = id
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.prev_x = float(x)
        self.prev_y = float(y)
        self.prev_z = float(z)
        self.vx = 0
        self.vy = 0
        self.actual_vx = 0.0
        self.actual_vy = 0.0
        self.last_vx = 0.0
        self.last_vy = 0.0
        self.radius = 35
        self.prop_angle = 0
        self.is_dragged = False

    def update(self):
        if not self.is_dragged:
            # Apply velocity
            self.x += self.vx
            self.y += self.vy
            
            # Simple friction/damping for smooth lerping behavior
            self.vx *= 0.85
            self.vy *= 0.85

        self.actual_vx = self.x - self.prev_x
        self.actual_vy = self.y - self.prev_y
        
        if abs(self.actual_vx) > 0.1 or abs(self.actual_vy) > 0.1:
            self.last_vx = self.actual_vx
            self.last_vy = self.actual_vy
            
        # Print coordinate changes to terminal
        if abs(self.actual_vx) > 0.1 or abs(self.actual_vy) > 0.1 or abs(self.z - self.prev_z) > 0.1:
            print(f"-> Drone {self.id} Position: x={self.x:.1f}, y={self.y:.1f}, z={self.z:.1f}")

        self.prev_x = self.x
        self.prev_y = self.y
        self.prev_z = self.z

        # Spin propellers constantly (faster)
        self.prop_angle += 25
        if self.prop_angle >= 360:
            self.prop_angle -= 360

    def draw(self, surface):
        arm_len = 28
        
        # Shadow effect
        pygame.draw.circle(surface, (15, 15, 20), (int(self.x) + 5, int(self.y) + 5), 15)
        
        # Draw arms (X shape)
        pygame.draw.line(surface, DRONE_ARM, (self.x - arm_len, self.y - arm_len), (self.x + arm_len, self.y + arm_len), 5)
        pygame.draw.line(surface, DRONE_ARM, (self.x + arm_len, self.y - arm_len), (self.x - arm_len, self.y + arm_len), 5)
        
        # Draw body
        pygame.draw.circle(surface, DRONE_BODY, (int(self.x), int(self.y)), 14)
        pygame.draw.circle(surface, (100, 100, 100), (int(self.x), int(self.y)), 14, 2)
        
        # Draw propellers
        prop_radius = 18
        centers = [
            (self.x - arm_len, self.y - arm_len),
            (self.x + arm_len, self.y - arm_len),
            (self.x - arm_len, self.y + arm_len),
            (self.x + arm_len, self.y + arm_len)
        ]
        
        for cx, cy in centers:
            # Propeller blur (semi-transparent disk)
            s = pygame.Surface((prop_radius*2, prop_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (150, 150, 150, 80), (prop_radius, prop_radius), prop_radius)
            surface.blit(s, (cx - prop_radius, cy - prop_radius))
            
            # Propeller rim
            pygame.draw.circle(surface, (120, 120, 120), (int(cx), int(cy)), prop_radius, 1)

            # High-speed spinning blades
            start_x = cx + math.cos(math.radians(self.prop_angle)) * prop_radius
            start_y = cy + math.sin(math.radians(self.prop_angle)) * prop_radius
            end_x = cx + math.cos(math.radians(self.prop_angle + 180)) * prop_radius
            end_y = cy + math.sin(math.radians(self.prop_angle + 180)) * prop_radius
            pygame.draw.line(surface, (30, 30, 30), (start_x, start_y), (end_x, end_y), 3)
            
            # Cross blades
            start_x2 = cx + math.cos(math.radians(self.prop_angle + 90)) * prop_radius
            start_y2 = cy + math.sin(math.radians(self.prop_angle + 90)) * prop_radius
            end_x2 = cx + math.cos(math.radians(self.prop_angle + 270)) * prop_radius
            end_y2 = cy + math.sin(math.radians(self.prop_angle + 270)) * prop_radius
            pygame.draw.line(surface, (30, 30, 30), (start_x2, start_y2), (end_x2, end_y2), 3)

        # ID label
        font = pygame.font.SysFont("Arial", 16, bold=True)
        text = font.render(f"D{self.id} ({int(self.x)}, {int(self.y)}, {int(self.z)})", True, TEXT_COLOR)
        surface.blit(text, (self.x - text.get_width()//2, self.y + 35))

class FPGA:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alert_timer = 0
        self.leader_id = 0
        
        # Base V formation coordinates
        # Reference point allows generating realistic offsets
        self.formation_base = {
            0: (0, 0),         # Tip of the V
            1: (-200, 150),    # Left flank
            2: (200, 150)      # Right flank
        }

    def update_formation(self, drones):
        dragged_id = None
        for d in drones:
            if d.is_dragged:
                dragged_id = d.id
                break
        
        # If someone is dragged, make them the new reference
        if dragged_id is not None:
            if self.leader_id != dragged_id:
                self.leader_id = dragged_id
                
        leader = drones[self.leader_id]
        
        # Calculate current global offset based on the leader's position
        base_lx, base_ly = self.formation_base[self.leader_id]
        offset_x = leader.x - base_lx
        offset_y = leader.y - base_ly
        
        # Adjust follower drones
        for d in drones:
            if d.id == self.leader_id:
                continue
                
            bx, by = self.formation_base[d.id]
            target_x = bx + offset_x
            target_y = by + offset_y
            
            error_x = target_x - d.x
            error_y = target_y - d.y
            
            # If a follower is misaligned and not being dragged, command it
            if (abs(error_x) > 3 or abs(error_y) > 3) and not d.is_dragged:
                # Proportional control (mimicking physical response)
                d.vx += error_x * 0.03
                d.vy += error_y * 0.03
                
                # Active correction triggers alert state
                self.alert_timer = 15

        if self.alert_timer > 0:
            self.alert_timer -= 1

    def draw(self, surface, drones, time_ticks):
        # Data paths
        for d in drones:
            # Background wire
            pygame.draw.line(surface, (60, 60, 80), (self.x, self.y), (d.x, d.y), 2)
            
            # Signal particles
            dx = d.x - self.x
            dy = d.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                speed = 1.5
                num_packets = 4
                for i in range(num_packets):
                    progress = ((time_ticks * speed + i * (100 / num_packets)) % 100) / 100.0
                    
                    if self.alert_timer > 0 and d.id != self.leader_id:
                        # Command signal: FPGA -> Follower Drone
                        px = self.x + dx * progress
                        py = self.y + dy * progress
                        color = SIGNAL_CMD
                        radius = 4
                    else:
                        # Telemetry signal: Drone -> FPGA
                        progress = 1.0 - progress
                        px = self.x + dx * progress
                        py = self.y + dy * progress
                        color = SIGNAL_TELEMETRY
                        radius = 3
                        
                    pygame.draw.circle(surface, color, (int(px), int(py)), radius)
                    # Glow effect
                    s = pygame.Surface((radius*4, radius*4), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*color, 100), (radius*2, radius*2), radius*2)
                    surface.blit(s, (int(px) - radius*2, int(py) - radius*2))

        # FPGA Hardware Box
        rect = pygame.Rect(self.x - 70, self.y - 45, 140, 90)
        box_color = ALERT_COLOR if self.alert_timer > 0 else FPGA_COLOR
        pygame.draw.rect(surface, box_color, rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), rect, 3, border_radius=8)
        
        # Status Text
        font = pygame.font.SysFont("Arial", 18, bold=True)
        text_f = font.render("FPGA CONTROLLER", True, (0, 0, 0) if self.alert_timer > 0 else (255,255,255))
        surface.blit(text_f, (self.x - text_f.get_width()//2, self.y - 25))
        
        font_small = pygame.font.SysFont("Arial", 14, bold=True)
        status = "ALERT: ADJUSTING" if self.alert_timer > 0 else "STATUS: STABLE"
        text_s = font_small.render(status, True, (0, 0, 0) if self.alert_timer > 0 else (200, 200, 200))
        surface.blit(text_s, (self.x - text_s.get_width()//2, self.y + 5))

def main():
    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Drone V-Formation & FPGA Interactive Sim")
    clock = pygame.time.Clock()

    # Initial positions matching the V shape natively
    drones = [
        Drone(0, WIDTH // 2, 200),
        Drone(1, WIDTH // 2 - 200, 350),
        Drone(2, WIDTH // 2 + 200, 350)
    ]
    
    fpga = FPGA(WIDTH // 2, HEIGHT - 100)
    
    dragging_drone = None
    time_ticks = 0
    
    active_tab = "absolute"  # "absolute" or "relative"

    running = True
    while running:
        time_ticks += 1
        SCREEN.fill(BG_COLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = event.pos
                    
                    # Check tab clicks first
                    table_x = WIDTH - 350
                    table_y = 20
                    if table_y <= my <= table_y + 30:
                        if table_x <= mx <= table_x + 160:
                            active_tab = "absolute"
                        elif table_x + 160 < mx <= table_x + 340:
                            active_tab = "relative"
                            
                    # Check collision with drone radius
                    for d in drones:
                        if math.hypot(d.x - mx, d.y - my) < d.radius + 15: # slightly larger click area
                            d.is_dragged = True
                            dragging_drone = d
                            break
                            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if dragging_drone:
                        dragging_drone.is_dragged = False
                        dragging_drone = None
            
            elif event.type == pygame.MOUSEMOTION:
                if dragging_drone:
                    mx, my = event.pos
                    dragging_drone.x = mx
                    dragging_drone.y = my

        # Process logic
        fpga.update_formation(drones)
        for d in drones:
            d.update()

        # Render everything
        
        # Drone-to-drone communication paths
        for i in range(len(drones)):
            for j in range(i + 1, len(drones)):
                d1 = drones[i]
                d2 = drones[j]
                # Faint line between drones
                pygame.draw.line(SCREEN, (50, 50, 60), (d1.x, d1.y), (d2.x, d2.y), 1)
                
                dx = d2.x - d1.x
                dy = d2.y - d1.y
                if math.hypot(dx, dy) > 0:
                    speed = 1.5
                    num_packets_d2d = 3
                    for k in range(num_packets_d2d):
                        # Packets D1 -> D2 (Orange)
                        prog1 = ((time_ticks * speed + k * (100 / num_packets_d2d)) % 100) / 100.0
                        px1 = d1.x + dx * prog1
                        py1 = d1.y + dy * prog1
                        pygame.draw.circle(SCREEN, (255, 140, 0), (int(px1), int(py1)), 2)
                        
                        # Packets D2 -> D1 (Purple)
                        prog2 = 1.0 - prog1
                        px2 = d1.x + dx * prog2
                        py2 = d1.y + dy * prog2
                        pygame.draw.circle(SCREEN, (200, 100, 255), (int(px2), int(py2)), 2)

        fpga.draw(SCREEN, drones, time_ticks)
        for d in drones:
            d.draw(SCREEN)
            
        # Draw instructions
        font_inst = pygame.font.SysFont("Arial", 16)
        inst_text = font_inst.render("Drag any drone with your mouse. The FPGA will re-position the others to maintain the V-formation.", True, (150, 150, 150))
        SCREEN.blit(inst_text, (20, 20))

        # --- Draw Tabbed Velocity Table ---
        table_x = WIDTH - 350
        table_y = 20
        row_height = 25
        
        # Draw table background
        box_height = 80 + row_height * len(drones)
        pygame.draw.rect(SCREEN, (30, 35, 45), (table_x - 10, table_y - 10, 340, box_height), border_radius=8)
        pygame.draw.rect(SCREEN, (100, 100, 120), (table_x - 10, table_y - 10, 340, box_height), 2, border_radius=8)

        # Draw Tabs
        tab_font = pygame.font.SysFont("Arial", 16, bold=True)
        
        # Absolute Tab
        abs_color = (80, 150, 255) if active_tab == "absolute" else (100, 100, 100)
        pygame.draw.rect(SCREEN, abs_color, (table_x, table_y, 150, 30), border_radius=5)
        abs_text = tab_font.render("Absolute Vel", True, (255, 255, 255))
        SCREEN.blit(abs_text, (table_x + 75 - abs_text.get_width()//2, table_y + 5))
        
        # Relative Tab
        rel_color = (80, 150, 255) if active_tab == "relative" else (100, 100, 100)
        pygame.draw.rect(SCREEN, rel_color, (table_x + 160, table_y, 150, 30), border_radius=5)
        rel_text = tab_font.render("Relative Vel", True, (255, 255, 255))
        SCREEN.blit(rel_text, (table_x + 160 + 75 - rel_text.get_width()//2, table_y + 5))

        font_table = pygame.font.SysFont("Courier New", 14)
        
        content_y = table_y + 40
        if active_tab == "absolute":
            header_str = "ID    Vx     Vy   Speed"
            header_text = font_table.render(header_str, True, (180, 180, 200))
            SCREEN.blit(header_text, (table_x, content_y))
            
            for idx, d in enumerate(drones):
                speed = math.hypot(d.last_vx, d.last_vy)
                row_str = f"D{d.id:<2} {d.last_vx:>+6.1f} {d.last_vy:>+6.1f} {speed:>6.1f}"
                color = (255, 215, 0) if d.id == fpga.leader_id else (200, 200, 200)
                row_text = font_table.render(row_str, True, color)
                SCREEN.blit(row_text, (table_x, content_y + row_height * (idx + 1)))
        else:
            header_str = "ID   R_Vx   R_Vy  R_Speed (to Lead)"
            header_text = font_table.render(header_str, True, (180, 180, 200))
            SCREEN.blit(header_text, (table_x, content_y))
            
            leader = drones[fpga.leader_id]
            for idx, d in enumerate(drones):
                rel_vx = d.last_vx - leader.last_vx
                rel_vy = d.last_vy - leader.last_vy
                rel_speed = math.hypot(rel_vx, rel_vy)
                
                row_str = f"D{d.id:<2} {rel_vx:>+6.1f} {rel_vy:>+6.1f} {rel_speed:>6.1f}"
                if d.id == leader.id:
                    row_str += "  [LEADER]"
                
                color = (255, 215, 0) if d.id == fpga.leader_id else (200, 200, 200)
                row_text = font_table.render(row_str, True, color)
                SCREEN.blit(row_text, (table_x, content_y + row_height * (idx + 1)))

        # ---------------------------

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
