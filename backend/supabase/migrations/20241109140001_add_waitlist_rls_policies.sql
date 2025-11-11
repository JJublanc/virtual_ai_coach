-- Migration: Add Row Level Security policies for waitlist table
-- Users can only read/write their own waitlist entries

-- Enable RLS on waitlist table
ALTER TABLE public.waitlist ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own waitlist entries
CREATE POLICY "Users can view their own waitlist entries"
  ON public.waitlist
  FOR SELECT
  USING (auth.uid() = user_id);

-- Policy: Users can insert their own waitlist entries
CREATE POLICY "Users can insert their own waitlist entries"
  ON public.waitlist
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own waitlist entries (e.g., update comment)
CREATE POLICY "Users can update their own waitlist entries"
  ON public.waitlist
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can delete their own waitlist entries
CREATE POLICY "Users can delete their own waitlist entries"
  ON public.waitlist
  FOR DELETE
  USING (auth.uid() = user_id);

-- Optional: Admin policy (if you have an admin role in the future)
-- This allows reading all waitlist entries for analytics
-- Uncomment when you implement admin roles:
-- CREATE POLICY "Admins can view all waitlist entries"
--   ON public.waitlist
--   FOR SELECT
--   USING (auth.jwt() ->> 'role' = 'admin');
