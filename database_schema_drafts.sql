-- Database Schema for Drafts and Draft Comments
-- This file contains the SQL statements to create the necessary tables for the drafts functionality

-- Drafts table
CREATE TABLE IF NOT EXISTS drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    visionboard_id UUID NOT NULL,
    user_id UUID NOT NULL,
    media_url TEXT NOT NULL,
    media_type VARCHAR(50), -- e.g., 'image', 'video', 'audio', 'document'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraints
    FOREIGN KEY (visionboard_id) REFERENCES visionboards(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes for better performance
    CREATE INDEX idx_drafts_visionboard_id ON drafts(visionboard_id);
    CREATE INDEX idx_drafts_user_id ON drafts(user_id);
    CREATE INDEX idx_drafts_created_at ON drafts(created_at DESC);
);

-- Draft Comments table
CREATE TABLE IF NOT EXISTS draft_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id UUID NOT NULL,
    user_id UUID NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraints
    FOREIGN KEY (draft_id) REFERENCES drafts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes for better performance
    CREATE INDEX idx_draft_comments_draft_id ON draft_comments(draft_id);
    CREATE INDEX idx_draft_comments_user_id ON draft_comments(user_id);
    CREATE INDEX idx_draft_comments_created_at ON draft_comments(created_at ASC);
);

-- Trigger to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic updated_at updates
CREATE TRIGGER update_drafts_updated_at 
    BEFORE UPDATE ON drafts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_draft_comments_updated_at 
    BEFORE UPDATE ON draft_comments 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments to tables for documentation
COMMENT ON TABLE drafts IS 'Stores media drafts uploaded by users for vision boards';
COMMENT ON TABLE draft_comments IS 'Stores comments made on drafts by vision board members';

COMMENT ON COLUMN drafts.media_url IS 'URL to the uploaded media file (e.g., Supabase Storage URL)';
COMMENT ON COLUMN drafts.media_type IS 'Type of media: image, video, audio, document, etc.';
COMMENT ON COLUMN drafts.description IS 'Optional description or caption for the draft';
COMMENT ON COLUMN draft_comments.comment IS 'The comment text made by a user on a draft'; 