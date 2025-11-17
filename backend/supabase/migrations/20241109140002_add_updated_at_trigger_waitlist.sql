-- Migration: Add trigger to automatically update updated_at timestamp

-- Create or replace the function to update the updated_at column
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for waitlist table
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.waitlist
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();
