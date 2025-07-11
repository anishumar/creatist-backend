-- Add visionboard_id column to posts table
ALTER TABLE posts ADD COLUMN visionboard_id UUID REFERENCES visionboards(id);

-- Add index for better performance
CREATE INDEX idx_posts_visionboard_id ON posts(visionboard_id);

-- Update existing posts to have NULL visionboard_id
-- (This is safe since we're adding a nullable column) 