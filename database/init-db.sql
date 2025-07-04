-- Create users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on username and email for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Update the updated_at column on every update
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    image_url VARCHAR(500),
    votes INTEGER DEFAULT 0
);

-- Create index on id for faster lookups
CREATE INDEX IF NOT EXISTS idx_products_id ON products(id);

-- Populate products table
-- This will not cause an error if the products already exist.
INSERT INTO products (id, name, description, image_url, votes) VALUES
(1, 'Origami Crane', 'Behold the delicate elegance of this Origami Crane, rendered in soft pastel hues that lend it an ethereal charm. The graceful arch of its wings and the poised curvature of its neck evoke a sense of serenity and balance. Each meticulously folded crease tells a story of patience and precision, capturing the essence of the traditional art of paper folding. The gentle gradient of its pink hue enhances its beauty, reflecting the transient glow of a setting sun. This paper masterpiece serves as a poignant symbol of peace, hope, and the intricate dance of art and nature.', '/static/images/origami/001-origami.png', 1),
(2, 'Origami Frog', 'Dive into the enchanting realm of the Origami Frog, a captivating representation of the amphibious wonders that inhabit our ponds and wetlands. This artful creation, with its bulging eyes and poised, springy legs, encapsulates the playful essence and sprightly demeanor of its real-life counterpart. Crafted with meticulous precision, each fold and crease brings to life the frog''s distinctive features, from its wide mouth to its textured back. Its poised stance, as if ready to leap into the next adventure, invites onlookers into a world where nature''s simple joys come alive through the magic of paper folding. The Origami Frog stands not just as a testament to the art of origami, but also as a delightful ode to the vibrant and lively spirit of these charming aquatic creatures.', '/static/images/origami/012-origami-8.png', 0),
(3, 'Origami Kangaroo', 'Step into the rugged landscapes of the Australian outback with our Origami Kangaroo, a masterful depiction of one of the continent''s most iconic marsupials. This paper creation, with its powerful hind legs and distinctive pouch, captures the unique essence and agile grace of the kangaroo. Each fold and contour meticulously represents its muscular build, upright posture, and the gentle curve of its tail, used for balance during those impressive leaps. The attentive gaze and erect ears portray an ever-alert nature, characteristic of these fascinating creatures. Beyond its aesthetic allure, the Origami Kangaroo is also a symbol of strength, adaptability, and the boundless wonders of the natural world, all wrapped into a single, intricate piece of art.', '/static/images/origami/010-origami-6.png', 0),
(4, 'Origami Camel', 'Journey into the sun-kissed dunes of the desert with our Origami Camel, a magnificent portrayal of the enduring giants that gracefully navigate the arid terrains. This artful masterpiece, with its humped back and long, graceful neck, perfectly encapsulates the camel''s resilience and elegance. Each meticulous fold and crease gives life to its broad feet, adapted for sandy travels, and the gentle curve of its distinctive humps, which are nature''s solution for long journeys without water. The poised stance and serene expression evoke images of golden horizons and the age-old tales of caravans that traverse vast landscapes under starry skies. The Origami Camel stands as a tribute to the majesty of these desert wanderers..', '/static/images/origami/021-camel.png', 0),
(5, 'Origami Butterfly', 'Witness the ephemeral beauty of our Origami Butterfly, a delicate creation symbolizing transformation and ethereal beauty. With wings that seem to flutter with an unspoken elegance, this piece allures eyes with its intricate patterns and gentle symmetries. Each fold carries with it a tale of metamorphosis, inviting you to embark upon a journey through blooming fields where these paper wonders flutter, leaving a trail of enchanted admirers in their gentle wake.', '/static/images/origami/017-origami-9.png', 0)
ON CONFLICT (id) DO NOTHING;
