import {createClient } from '@supabase/supabase-js'

const url = process.env.SB_URL;
const anon = process.env.SB_ANON;

export const supabase = createClient(url,anon);