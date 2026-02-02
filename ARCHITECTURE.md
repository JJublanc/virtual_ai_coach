# Virtual AI Coach - Complete Architecture Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Application Structure](#application-structure)
5. [Core Components](#core-components)
6. [Data Models](#data-models)
7. [API Endpoints](#api-endpoints)
8. [Video Processing Pipeline](#video-processing-pipeline)
9. [Frontend Architecture](#frontend-architecture)
10. [Authentication & User Management](#authentication--user-management)
11. [Database Schema](#database-schema)
12. [Configuration & Environment](#configuration--environment)
13. [Deployment & Infrastructure](#deployment--infrastructure)
14. [Key Design Principles](#key-design-principles)
15. [Development Workflow](#development-workflow)

---

## Project Overview

**Virtual AI Coach** is a free, AI-powered fitness application that generates personalized workout videos in real-time. Users can configure their workout preferences (intensity, exercise types, duration) and the application dynamically creates custom video workouts by concatenating pre-recorded exercise clips with intelligent overlays (timer, progress bar, exercise names).

### Key Features

- **AI-Powered Workout Generation**: Automatically generates workout sequences based on user preferences
- **Real-Time Video Streaming**: Generates and streams personalized workout videos on-demand
- **Exercise Catalog**: 100+ bodyweight exercises with video demonstrations
- **Customizable Workouts**:
  - Intensity levels (low-impact, medium, high)
  - Work/rest intervals
  - Duration targets
  - Exercise filters (no-jump, difficulty level)
  - Block-based structure (thematic workout blocks)
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Freemium Model**: Core features free, premium exercises planned for Phase 2

### Target Users

- Fitness beginners looking for guided workouts
- Home gym enthusiasts without equipment
- Users seeking personalized, adaptive training programs

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FRONTEND - Next.js 16                          │
│  ├─ Pages: Home, Train, Goals, Plan                             │
│  ├─ Components: Video Player, Exercises, Controls               │
│  ├─ State: Zustand Store                                        │
│  ├─ Styling: Tailwind CSS + Shadcn/ui                           │
│  └─ Deployment: Vercel                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                 HTTP/REST API (CORS enabled)
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND - FastAPI (Python 3.13+)                    │
│  ├─ API Layer: exercises.py, workouts.py                        │
│  ├─ Services:                                                   │
│  │   ├─ VideoService: Base video operations                     │
│  │   ├─ OptimizedVideoService: FFmpeg streaming                 │
│  │   └─ WorkoutGenerator: Exercise selection logic              │
│  ├─ Models: Exercise, Workout, WorkoutConfig                    │
│  └─ Deployment: Railway                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
    ┌────────┐          ┌─────────┐          ┌──────────┐
    │FFmpeg  │          │Supabase │          │ Exercise │
    │Process │          │ Client  │          │ JSON     │
    └────────┘          └─────────┘          └──────────┘
        │                    │
        ▼                    ▼
   ┌──────────────┐    ┌──────────────┐
   │ Video Output │    │PostgreSQL DB │
   │ (MP4 Stream) │    │(Supabase)    │
   └──────────────┘    └──────────────┘
```

### Data Flow: Workout Generation

```
1. User Input
   └─> Select exercises and configure workout

2. API Request
   └─> POST /api/generate-auto-workout-video
       {
         config: WorkoutConfig,
         total_duration: int
       }

3. Backend Processing
   ├─> Load exercises from Supabase/JSON
   ├─> Filter by criteria (no-jump, difficulty)
   ├─> Generate optimal workout sequence
   └─> Build FFmpeg command

4. Video Generation & Streaming
   ├─> FFmpeg processes exercises
   ├─> Applies speed adjustments (intensity)
   ├─> Adds overlays (timer, progress, names)
   ├─> Streams chunks to frontend
   └─> Frontend displays in HTML5 player

5. User Experience
   └─> Plays personalized workout video in browser
```

---

## Technology Stack

### Frontend

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Framework | Next.js | 16.0 | React app framework with built-in optimization |
| Language | TypeScript | 5.x | Type-safe frontend code |
| Styling | Tailwind CSS | 4.x | Utility-first CSS framework |
| UI Components | Shadcn/ui | 0.0.4 | Pre-built accessible components |
| State Management | Zustand | 5.0+ | Simple, lightweight state store |
| Data Fetching | TanStack Query | 5.90+ | Server state management, caching |
| Video Player | React Player | 3.3.3 | Cross-browser video playback |
| Icons | Lucide React | 0.548 | Consistent icon library |
| Validation | Zod | 4.1+ | Type-safe schema validation |
| Environment | dotenv | 17.2+ | Environment variable management |

### Backend

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Framework | FastAPI | 0.120+ | Modern async Python web framework |
| Language | Python | 3.13+ | Server-side logic and AI integration |
| Video Processing | FFmpeg | Latest | Video concatenation, encoding, filters |
| FFmpeg Python Wrapper | ffmpeg-python | 0.2.0 | Python bindings for FFmpeg |
| Video Library | MoviePy | 2.2.1 | Video composition and effects |
| Image Processing | OpenCV | 4.12+ | Image manipulation for overlays |
| Image Library | Pillow | 11.3+ | Image creation and modification |
| NumPy | NumPy | 2.2+ | Numerical operations |
| Database Client | Supabase | 2.24+ | PostgreSQL client with Auth |
| HTTP Client | aiohttp | 3.13+ | Async HTTP requests |
| Server | Uvicorn | 0.38+ | ASGI server for FastAPI |
| Config | python-dotenv | 1.1+ | Load environment variables |
| CLI | Typer | 0.20+ | CLI application framework |
| Request Handler | python-multipart | 0.0.20 | File upload handling |

### Infrastructure & Deployment

| Component | Technology | Cost | Purpose |
|-----------|-----------|------|---------|
| Frontend Hosting | Vercel | Free | Next.js optimized deployment |
| Backend Hosting | Railway | $0-10/mo | Python app deployment with databases |
| Database | Supabase PostgreSQL | Free (500MB) | Relational database with built-in auth |
| Storage | Supabase Storage | Free (1GB) | Exercise video storage with CDN |
| CDN | Supabase CDN | Included | Video delivery optimization |
| Domain | OVH/Namecheap | ~10€/year | Domain registration |
| Monitoring | Sentry | Free (5K events) | Error tracking and monitoring |

---

## Application Structure

### Directory Layout

```
virtual-ai-coach/
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── main.py                   # Application entry point
│   │   ├── api/                      # API endpoints
│   │   │   ├── exercises.py          # Exercise endpoints (GET /api/exercises)
│   │   │   └── workouts.py           # Workout generation endpoints
│   │   ├── services/                 # Business logic
│   │   │   ├── video_service.py      # Base video operations
│   │   │   ├── video_service_optimized.py  # FFmpeg optimization
│   │   │   └── workout_generator.py  # Exercise selection logic
│   │   ├── models/                   # Data models
│   │   │   ├── exercise.py           # Exercise model with metadata
│   │   │   ├── workout.py            # Workout session model
│   │   │   ├── config.py             # WorkoutConfig and BlockConfig
│   │   │   ├── enums.py              # Status, Intensity enums
│   │   │   └── exercises.json        # Exercise catalog (fallback)
│   │   └── config/                   # Configuration
│   │       └── break_videos.py       # Break video configurations
│   ├── supabase/                     # Database migrations
│   ├── scripts/                      # Utility scripts
│   ├── tests/                        # Test suite
│   ├── .env                          # Environment variables
│   ├── .env.example                  # Template for env vars
│   ├── requirements.txt              # Python dependencies
│   └── Procfile                      # Railway deployment config
│
├── frontend/                         # Next.js React frontend
│   ├── app/
│   │   ├── page.tsx                  # Landing page
│   │   ├── layout.tsx                # Root layout with providers
│   │   ├── globals.css               # Global styles
│   │   ├── (routes)/                 # Page routes
│   │   │   ├── train/                # Workout generation page
│   │   │   ├── goals/                # Goal selection page
│   │   │   └── plan/                 # Workout planning page
│   │   └── api/                      # Server-side API routes (if any)
│   ├── components/                   # React components
│   │   ├── layout/                   # Layout components
│   │   ├── video/                    # Video player components
│   │   ├── controls/                 # Workout controls
│   │   ├── exercises/                # Exercise selection components
│   │   └── modals/                   # Modal dialogs
│   ├── lib/                          # Utility functions
│   │   ├── api.ts                    # API client functions
│   │   ├── types.ts                  # TypeScript type definitions
│   │   ├── supabase.ts               # Supabase client config
│   │   └── utils.ts                  # Helper utilities
│   ├── hooks/                        # Custom React hooks
│   ├── providers/                    # Context providers
│   ├── store/                        # Zustand state stores
│   ├── public/                       # Static assets
│   ├── .env.local                    # Frontend environment variables
│   ├── next.config.ts                # Next.js configuration
│   ├── tailwind.config.ts            # Tailwind CSS config
│   ├── tsconfig.json                 # TypeScript config
│   └── package.json                  # Dependencies
│
├── docs/                             # Documentation
│   ├── architecture_globale.md       # System architecture
│   ├── database_schema_diagram.md    # Database schema
│   ├── api_documentation.md          # API reference
│   ├── workout_block_generation.md   # Block-based generation
│   └── [other docs]                  # Implementation guides
│
├── exercices_generation/             # Exercise video generation (legacy)
├── supabase/                         # Database migrations and config
├── videos_raw/                       # Raw exercise video files
├── videos_trimmed_60s/               # Trimmed to 60 seconds
├── videos_assets_youtube/            # YouTube asset videos
│
├── pyproject.toml                    # Python project config
├── requirements.txt                  # Python dependencies (compiled)
├── railway.json                      # Railway deployment config
├── Procfile                          # Heroku/Railway entry point
├── nixpacks.toml                     # Nixpacks configuration
├── README.md                         # Project README
└── ARCHITECTURE.md                   # This file
```

---

## Core Components

### 1. Backend API Layer (`app/api/`)

#### exercises.py
- **Purpose**: Manage exercise catalog operations
- **Key Functions**:
  - `GET /api/exercises` - List all exercises with caching
  - `GET /api/exercises/{name}` - Get specific exercise
- **Data Source**: Configurable (JSON or Supabase)
- **Caching**: HTTP Cache-Control headers (1 hour)

#### workouts.py
- **Purpose**: Handle workout generation and streaming
- **Key Functions**:
  - `POST /api/generate-auto-workout-video` - Auto-generate and stream workout
  - `POST /api/generate-workout-video` - Generate from specific exercises
- **Features**:
  - Streaming response with chunked video data
  - Custom HTTP headers (X-Workout-ID, X-Exercise-Count)
  - Timeout protection (300s)
  - Error handling and validation

### 2. Service Layer (`app/services/`)

#### VideoService (video_service.py)
- **Purpose**: Base video operations abstraction
- **Responsibilities**:
  - Video trimming via FFmpeg
  - Cache management for Supabase videos
  - URL downloading and local caching
  - Basic video format detection

#### OptimizedVideoService (video_service_optimized.py)
- **Purpose**: High-performance video streaming
- **Key Features**:
  - Progressive concatenation by chunks
  - Stream copy optimization (H.264 detection)
  - Pre-generated break video cache
  - Parallel video downloads (ThreadPoolExecutor)
  - Memory cleanup during streaming
  - Format normalization (1280x720 H.264 @ 30fps)

#### WorkoutGenerator (workout_generator.py)
- **Purpose**: Intelligent exercise selection
- **Responsibilities**:
  - Load exercises from JSON/Supabase
  - Filter by criteria (no-jump, difficulty, type)
  - Handle block-based generation
  - Calculate workout structure
  - Ensure no-repeat logic
  - Balance exercise themes (upper body, legs, cardio, abs)

### 3. Models (`app/models/`)

#### exercise.py
```python
class Exercise(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    icon: Optional[str]
    video_url: str
    thumbnail_url: Optional[str]
    default_duration: int
    difficulty: Difficulty  # easy, medium, hard
    has_jump: bool
    access_tier: AccessTier  # free, premium
    metadata: Optional[ExerciseMetadata]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
```

#### config.py
```python
class WorkoutConfig(BaseModel):
    intensity: Intensity  # low_impact, medium_intensity, high_intensity
    intervals: Dict[str, int]  # {work_time, rest_time}
    no_repeat: bool
    no_jump: bool
    exercice_intensity_levels: List[Difficulty]
    include_warm_up: bool
    include_cool_down: bool
    target_duration: int  # minutes
    show_timer: bool
    show_progress_bar: bool
    show_exercise_name: bool
    exercise_type: Optional[str]  # Filter by type
    use_block_structure: bool
    block_config: Optional[BlockConfig]
```

#### workout.py
```python
class Workout(BaseModel):
    id: Optional[UUID]
    user_id: Optional[UUID]  # NULL for anonymous
    name: Optional[str]
    config: WorkoutConfig
    total_duration: Optional[int]
    ai_generated: bool
    ai_prompt: Optional[str]
    status: Status  # draft, ready, in_progress, completed
    video_url: Optional[str]
    session_token: Optional[str]  # For anonymous sessions
    expires_at: Optional[datetime]
    exercises: Optional[List[WorkoutExercise]]
```

### 4. Enums (`app/models/enums.py`)

```python
class Status(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class Intensity(str, Enum):
    LOW_IMPACT = "low_impact"
    MEDIUM_INTENSITY = "medium_intensity"
    HIGH_INTENSITY = "high_intensity"

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class ExerciseTheme(str, Enum):
    UPPER_BODY = "upper_body"
    LEGS = "legs"
    CARDIO = "cardio"
    ABS = "abs"
    FULL_BODY = "full_body"
```

---

## Data Models

### Core Entities

#### Exercise
- **Properties**: Name, description, video URL, difficulty, duration, jump flag, themes
- **Relationships**: Many-to-many with categories, one-to-many with workouts
- **Storage**: Supabase table `exercises`
- **Metadata**: JSON with muscles targeted, calories per minute, alternative exercises

#### Workout
- **Properties**: Name, config (JSONB), status, duration, AI flag
- **Relationships**: One-to-many with workout_exercises
- **Storage**: Supabase table `workouts`
- **Key Feature**: Anonymous sessions via `session_token` with 24h expiry

#### WorkoutExercise
- **Properties**: Exercise ID, workout ID, order index, custom duration
- **Relationships**: Links exercises to workouts
- **Storage**: Supabase table `workout_exercises`

#### User Profile (Phase 2)
- **Properties**: Display name, avatar, fitness level, preferences, subscription status
- **Relationships**: One-to-many with workouts and sessions
- **Storage**: Supabase table `user_profiles`
- **Stripe Integration**: Subscription management

#### WorkoutSession (Phase 2)
- **Properties**: Started/completed timestamps, duration, exercises completed, feedback
- **Purpose**: Track user workout history
- **Storage**: Supabase table `workout_sessions`

---

## API Endpoints

### Exercise Management

```http
GET /api/exercises
├─ Description: List all available exercises
├─ Cache: 1 hour (public)
└─ Response: Exercise[]

GET /api/exercises/{exercise_name}
├─ Description: Get specific exercise by name (case-insensitive)
├─ Parameters: exercise_name (string)
└─ Response: Exercise | 404 if not found
```

### Workout Generation

```http
POST /api/generate-auto-workout-video
├─ Description: Auto-generate workout and stream video
├─ Request Body:
│  ├─ config: WorkoutConfig (required)
│  ├─ total_duration: int (required, seconds)
│  └─ name: string (optional)
├─ Response: StreamingResponse (video/mp4)
├─ Headers Returned:
│  ├─ X-Workout-ID: Unique workout ID
│  └─ X-Exercise-Count: Number of exercises
└─ Timeout: 300 seconds

POST /api/generate-workout-video
├─ Description: Generate video from exercise list
├─ Request Body:
│  ├─ exercise_names: List[str] (required)
│  └─ config: WorkoutConfig (optional)
├─ Response: StreamingResponse (video/mp4)
└─ Timeout: 300 seconds
```

### Health & Status

```http
GET /health
├─ Description: Server health check
└─ Response: {"status": "healthy", "message": "..."}

GET /
└─ Description: Redirects to /docs (Swagger UI)
```

---

## Video Processing Pipeline

### FFmpeg-Based Workflow

```
Exercise Videos (MOV, 60s, 1280x720)
    │
    ├─ Load from Supabase or local disk
    │
    ├─ Video Format Detection
    │  ├─ Codec (H.264, VP9, etc.)
    │  ├─ Resolution (normalize to 1280x720)
    │  ├─ FPS (normalize to 30fps)
    │  └─ Bitrate
    │
    ├─ Adjust Speed (Intensity)
    │  ├─ Low Impact (80%): setpts='0.8*PTS'
    │  ├─ Medium (100%): No change
    │  └─ High (120%): setpts='1.2*PTS'
    │
    ├─ Trim to Duration (Work time)
    │  └─ Concatenate with rest/break videos
    │
    ├─ Add Overlays
    │  ├─ Timer: drawtext with current timestamp
    │  ├─ Progress Bar: drawbox with width = (current_time / total_time) * video_width
    │  └─ Exercise Name: drawtext with exercise name
    │
    ├─ Stream Output
    │  ├─ Format: MP4
    │  ├─ Codec: H.264 (libx264)
    │  ├─ Preset: ultrafast (low latency)
    │  ├─ CRF: 23 (quality/size balance)
    │  ├─ Pixel Format: yuv420p
    │  └─ Flags: frag_keyframe+empty_moov (streaming)
    │
    └─ Chunked Delivery
        ├─ 64KB chunks to frontend
        ├─ HTML5 video player buffers
        └─ Progressive playback
```

### Key Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Resolution | 1280x720 | Optimal for mobile/desktop |
| Frame Rate | 30 fps | Smooth playback |
| Codec | H.264 | Universal browser support |
| Preset | ultrafast | Minimize latency |
| CRF | 23 | Quality 0-51 scale |
| Chunk Size | 64KB | Progressive delivery |

### Performance Optimizations

1. **Stream Copy**: Skip re-encoding if format matches target
2. **Parallel Downloads**: Load up to 4 videos simultaneously from Supabase
3. **Break Video Cache**: Pre-generated rest periods cached by duration
4. **Incremental Cleanup**: Remove temp files as chunks stream
5. **Memory Management**: Process in chunks to avoid RAM spikes

---

## Frontend Architecture

### Pages (Routes)

#### Landing Page (`/`)
- Hero section with CTA
- FAQ with Schema.org markup for SEO
- Features overview
- Call-to-action to train page

#### Train Page (`/train`)
- Main workout generation interface
- Exercise selection UI
- Configuration options
- Video player with streaming
- Workout controls (play, pause, skip)

#### Goals Page (`/goals`)
- Goal selection interface
- Fitness level assessment
- Preference configuration

#### Plan Page (`/plan`)
- Workout history
- Saved programs
- Recovery tracking

### Component Architecture

```
App
├── Layout
│   ├── Header
│   │   ├── Logo
│   │   ├── Navigation
│   │   └── Auth Button
│   └── MainLayout
│       └── [Page Content]
│
├── Pages
│   ├── Home
│   ├── Train
│   │   ├── ExerciseSelector
│   │   ├── ConfigurationPanel
│   │   └── VideoPlayer
│   ├── Goals
│   └── Plan
│
├── Components (Shared)
│   ├── Video
│   │   └── WorkoutPlayer
│   ├── Controls
│   │   ├── IntensitySlider
│   │   ├── DurationSelector
│   │   └── PlaybackControls
│   ├── Exercises
│   │   ├── ExerciseCard
│   │   ├── ExerciseFilter
│   │   └── ExerciseList
│   └── Modals
│       └── [Various modals]
│
├── Hooks
│   ├── useWorkoutStore()
│   ├── useVideoPlayer()
│   └── useExercises()
│
├── Stores (Zustand)
│   ├── workoutStore
│   ├── userStore
│   └── uiStore
│
└── Providers
    ├── AuthProvider
    ├── ComingSoonProvider
    └── QueryClientProvider
```

### State Management (Zustand)

```typescript
// workoutStore
{
  config: WorkoutConfig
  exercises: Exercise[]
  selectedExercises: Exercise[]
  setConfig: (config) => void
  addExercise: (ex) => void
  removeExercise: (ex) => void
  clearWorkout: () => void
}

// userStore
{
  user: User | null
  fitnessLevel: FitnessLevel
  preferences: UserPreferences
  setUser: (user) => void
  updatePreferences: (prefs) => void
}
```

### API Integration

All API calls flow through `lib/api.ts`:

```typescript
export async function generateAutoWorkoutVideo(
  request: GenerateAutoWorkoutRequest
): Promise<Blob>

export function downloadBlob(blob: Blob, filename: string): void
```

### Styling Architecture

- **Global Styles**: `globals.css` with Tailwind directives
- **Component Styles**: Inline Tailwind classes (utility-first)
- **UI Components**: Shadcn/ui pre-built components
- **Custom Styling**: Post CSS v4 with Tailwind v4

### SEO Implementation

- Schema.org structured data (Organization, WebApplication, FAQ)
- Meta tags (title, description, og:, twitter:)
- Sitemap generation
- Canonical URLs
- Robots meta configuration

---

## Authentication & User Management

### Current Implementation (Phase 1)

**Anonymous Sessions**:
- No authentication required
- 24-hour session token
- Works entirely in frontend
- Stored in browser localStorage

**User Tracking**:
- Session token in URL params or localStorage
- Anonymous workouts linked to session_token
- Automatic cleanup after 24 hours

### Phase 2: Supabase Auth Integration

```typescript
// Planned structure
type User = {
  id: UUID
  email: string
  profile: UserProfile
  subscription: Subscription
  createdAt: datetime
}

// OAuth providers: Google, GitHub, Apple
// Email/password option
// JWT tokens for API requests
```

### Future: Subscription Management

- Stripe integration for payments
- Subscription tiers: Free, Premium, Pro
- Premium exercise access
- Advanced features unlock
- Usage tracking and limits

---

## Database Schema

### Primary Tables

#### exercises
```sql
CREATE TABLE exercises (
  id UUID PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  icon VARCHAR(50),
  video_url TEXT NOT NULL,
  thumbnail_url TEXT,
  default_duration INTEGER NOT NULL,
  difficulty VARCHAR(20),  -- easy, medium, hard
  has_jump BOOLEAN DEFAULT false,
  access_tier VARCHAR(20) DEFAULT 'free',  -- free, premium
  metadata JSONB,  -- {"muscles_targeted", "calories_per_min"}
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_exercises_difficulty ON exercises(difficulty);
CREATE INDEX idx_exercises_access_tier ON exercises(access_tier);
CREATE INDEX idx_exercises_metadata ON exercises USING gin(metadata);
```

#### workouts
```sql
CREATE TABLE workouts (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),  -- NULL for anonymous
  name VARCHAR(100),
  config JSONB NOT NULL,  -- WorkoutConfig
  total_duration INTEGER,
  ai_generated BOOLEAN DEFAULT false,
  ai_prompt TEXT,
  status VARCHAR(20) DEFAULT 'draft',  -- draft, ready, in_progress, completed
  video_url TEXT,
  session_token VARCHAR(255),  -- For anonymous sessions
  expires_at TIMESTAMPTZ,  -- 24h from creation
  created_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_workouts_user_id ON workouts(user_id);
CREATE INDEX idx_workouts_session_token ON workouts(session_token);
CREATE INDEX idx_workouts_expires_at ON workouts(expires_at);
```

#### workout_exercises
```sql
CREATE TABLE workout_exercises (
  id UUID PRIMARY KEY,
  workout_id UUID REFERENCES workouts(id) ON DELETE CASCADE,
  exercise_id UUID REFERENCES exercises(id) ON DELETE RESTRICT,
  order_index INTEGER NOT NULL,
  custom_duration INTEGER,
  UNIQUE(workout_id, order_index)
);

-- Indexes
CREATE INDEX idx_workout_exercises_workout ON workout_exercises(workout_id);
CREATE INDEX idx_workout_exercises_exercise ON workout_exercises(exercise_id);
```

#### Categories & Relationships (Phase 2)
```sql
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL,
  description TEXT
);

CREATE TABLE exercise_categories (
  exercise_id UUID REFERENCES exercises(id) ON DELETE CASCADE,
  category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
  PRIMARY KEY (exercise_id, category_id)
);
```

### Queries

**Get all exercises for user**:
```sql
SELECT e.* FROM exercises e
WHERE e.access_tier = 'free'
  OR (e.access_tier = 'premium' AND EXISTS (
    SELECT 1 FROM user_profiles up
    WHERE up.id = $1 AND up.subscription_status = 'active'
  ));
```

**Get complete workout with exercises**:
```sql
SELECT w.*,
  json_agg(json_build_object(
    'exercise', row_to_json(e.*),
    'order', we.order_index,
    'custom_duration', we.custom_duration
  ) ORDER BY we.order_index) as exercises
FROM workouts w
LEFT JOIN workout_exercises we ON w.id = we.workout_id
LEFT JOIN exercises e ON we.exercise_id = e.id
WHERE w.id = $1
GROUP BY w.id;
```

---

## Configuration & Environment

### Backend (.env)

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Feature Flags
USE_SUPABASE=true

# Video Cache
VIDEO_CACHE_DIR=/tmp/exercise_videos
VIDEO_CACHE_MAX_SIZE_GB=5

# API
API_PORT=8000
API_HOST=0.0.0.0

# Environment
PROJECT_ROOT=/path/to/project
```

### Frontend (.env.local)

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
```

### Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Visit http://localhost:3000
```

---

## Deployment & Infrastructure

### Frontend Deployment (Vercel)

**Configuration**:
- Framework: Next.js
- Node.js version: 20+
- Build command: `next build`
- Start command: `next start`
- Environment variables: See `.env.local.example`

**Deployment Process**:
1. Push to GitHub
2. Vercel auto-deploys on push
3. Preview deployments for pull requests
4. Production deployment for main branch

**Domain Setup**:
```
Frontend: https://tyswee.com (CNAME → vercel.com)
API: https://api.tyswee.com (CNAME → railway.app)
```

### Backend Deployment (Railway)

**Configuration** (`railway.json`):
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Environment Variables** (Set in Railway Dashboard):
- SUPABASE_URL
- SUPABASE_ANON_KEY
- USE_SUPABASE=true

**Deployment Process**:
1. Push to GitHub
2. Railway auto-deploys
3. Automatic health checks every 30s
4. Auto-restart on failure (max 10 retries)

### Database (Supabase)

**Free Tier Limits**:
- 500MB database storage
- 1GB file storage
- 2GB bandwidth per month
- Auth: Up to 50,000 users

**Production Considerations**:
- Upgrade to Pro tier ($25/month) at 500MB storage
- Includes 100GB storage, 100GB bandwidth
- Daily automated backups
- Point-in-time recovery

### Architecture Scaling Phases

**Phase 1 - MVP (0-100 users)**:
- Frontend: Vercel Free
- Backend: Railway Free (512MB RAM)
- Database: Supabase Free (500MB)
- Total: $0/month

**Phase 2 - Growth (100-1000 users)**:
- Frontend: Vercel Free/Pro ($20/month)
- Backend: Railway Hobby ($10/month, 8GB RAM)
- Database: Supabase Pro ($25/month, 100GB)
- Storage: Included in Supabase Pro
- Total: $10-55/month

**Phase 3 - Scale (1000+ users)**:
- Frontend: Vercel Pro + CDN
- Backend: Multiple Railway instances + load balancer
- Database: Supabase or managed PostgreSQL
- Cache: Redis cluster
- Storage: Backblaze B2 + Cloudflare CDN
- Total: $100-500+/month

---

## Key Design Principles

### 1. Performance First

- **Streaming**: Video streamed in chunks for progressive playback
- **Caching**: HTTP caching, browser caching, Supabase CDN
- **Optimization**: FFmpeg ultrafast preset, H.264 codec
- **Lazy Loading**: Components and data loaded on-demand

### 2. Scalability

- **Stateless Backend**: No session state, can run multiple instances
- **Async/Await**: All I/O operations non-blocking
- **Horizontal Scaling**: Add more servers without code changes
- **Database Indexing**: Strategic indexes on frequent queries

### 3. User Experience

- **Real-Time Feedback**: Streaming UI updates during generation
- **Responsive Design**: Mobile-first, works on all devices
- **Accessibility**: WCAG 2.1 AA compliance targets
- **Error Handling**: Graceful failures with user-friendly messages

### 4. Code Quality

- **Type Safety**: TypeScript frontend, Pydantic backend
- **Testing**: Unit tests, integration tests, E2E tests
- **Documentation**: Comprehensive inline comments and docs
- **Linting**: ESLint, Ruff for code quality

### 5. Security

- **Input Validation**: Pydantic models, Zod schemas
- **CORS**: Configured for specific origins
- **HTTPS**: Enforced in production
- **Rate Limiting**: Planned for Phase 2
- **Authentication**: JWT tokens (Phase 2)

### 6. Maintainability

- **Modular Structure**: Clear separation of concerns
- **Dependency Injection**: Configurable services
- **Configuration Management**: Environment-based config
- **Error Logging**: Structured logging with Sentry

---

## Development Workflow

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/jjublanc/virtual-ai-coach.git
cd virtual-ai-coach

# 2. Setup backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Setup frontend
cd ../frontend
npm install

# 4. Create .env files
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# 5. Configure environment variables
# Edit backend/.env and frontend/.env.local with local values

# 6. Start services in separate terminals

# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev

# Visit http://localhost:3000
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/workout-generation

# Make changes
# Commit with meaningful messages
git commit -m "feat: implement block-based workout generation"

# Push to GitHub
git push origin feature/workout-generation

# Create Pull Request
# Wait for code review and CI checks

# Merge to dev when approved
# Vercel Preview deployment auto-generated
# Manual testing on preview

# Merge to main for production deployment
```

### Testing Strategy

**Backend**:
```bash
cd backend
pytest tests/  # Run all tests
pytest tests/test_video_service.py  # Specific test file
pytest -v --cov  # With coverage
```

**Frontend**:
```bash
cd frontend
npm run lint  # ESLint
npm test  # Jest tests (if configured)
```

### Debugging

**Backend**:
- Uvicorn debug mode with `--reload`
- FastAPI Swagger UI at `/docs`
- Logs visible in terminal
- Sentry for production errors

**Frontend**:
- Next.js dev server with fast refresh
- Chrome DevTools
- React Developer Tools extension
- Console for debugging

### Performance Monitoring

**Backend**:
- Response time logging
- FFmpeg process timing
- Database query performance
- Memory usage monitoring

**Frontend**:
- Lighthouse scores
- Core Web Vitals
- Bundle size tracking
- User interaction metrics

---

## File Reference

### Key Backend Files

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `app/main.py` | App initialization | FastAPI app, CORS config |
| `app/api/exercises.py` | Exercise endpoints | get_exercises(), get_exercise_by_name() |
| `app/api/workouts.py` | Workout generation | generate_auto_workout_video() |
| `app/services/workout_generator.py` | Logic | generate_workout_exercises(), filter_exercises() |
| `app/services/video_service.py` | Base video ops | VideoService class |
| `app/services/video_service_optimized.py` | Streaming | OptimizedVideoService class |
| `app/models/exercise.py` | Data model | Exercise, ExerciseMetadata |
| `app/models/config.py` | Config model | WorkoutConfig, BlockConfig |
| `app/models/workout.py` | Workout model | Workout, WorkoutSession |

### Key Frontend Files

| File | Purpose | Key Exports |
|------|---------|------------|
| `app/layout.tsx` | Root layout | Providers, metadata |
| `app/page.tsx` | Landing page | Home component |
| `app/(routes)/train/page.tsx` | Workout generator | Train page |
| `lib/api.ts` | API client | generateAutoWorkoutVideo() |
| `lib/types.ts` | Type definitions | Exercise, WorkoutConfig, etc. |
| `components/video/WorkoutPlayer.tsx` | Video player | Video playback logic |
| Store files | State management | Zustand stores |

---

## Quick Reference

### Common Commands

```bash
# Backend
uvicorn backend.app.main:app --reload      # Dev server
python -m pytest tests/                    # Run tests
pip install -r requirements.txt            # Install deps

# Frontend
npm run dev                                # Dev server
npm run build                              # Production build
npm run lint                               # Check code quality
npm test                                   # Run tests
```

### API Examples

```bash
# Get exercises
curl http://localhost:8000/api/exercises

# Generate workout video
curl -X POST http://localhost:8000/api/generate-auto-workout-video \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "intensity": "medium_intensity",
      "intervals": {"work_time": 40, "rest_time": 20},
      "no_jump": false
    },
    "total_duration": 600
  }' > workout.mp4
```

### Environment Variables

**Backend**:
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
- `USE_SUPABASE`: Enable/disable Supabase

**Frontend**:
- `NEXT_PUBLIC_API_URL`: Backend API base URL

---

## Historique et Événements Majeurs

### Chronologie de Développement

#### **Décembre 2025 - Fondations du Projet**

**01 Décembre 2025 - Configuration Initiale**
- **Commit**: `521a7d3` - Ajout du nom de domaine aux configurations CORS
- **Décision**: Mise en place de l'infrastructure de déploiement (Railway + Vercel)
- **Impact**: Permet les requêtes cross-origin pour l'API backend
- **Fichiers**: `backend/app/main.py`

**02-05 Décembre 2025 - Optimisations Performances**
- **Commits**:
  - `b40bc1e` - Optimisation de la recherche d'exercices
  - `699fd15` - Ajout de logs de profilage du processus de génération vidéo
  - `842bf6c` - Optimisation de la génération de breaks
- **Décision Technique**: Introduction du système de cache pour les vidéos de pause
- **Gain de Performance**: Réduction de 2-3 secondes par pause générée
- **Fichiers**: `backend/app/services/video_service_optimized.py`, `backend/app/config/break_videos.py`

**05 Décembre 2025 - Refactoring Break Generation**
- **Commit**: `14e9c3c` - Nouvelle méthode pour générer les breaks
- **Décision**: Migration vers un système de breaks pré-générés stockés sur Supabase
- **Raison**: Éliminer la génération à la volée pour améliorer les temps de réponse
- **Impact**: Architecture centrée sur le cache pour les assets répétitifs
- **Documentation**: `/docs/workout_video_optimization_guide.md`

**16-19 Décembre 2025 - Sécurité et Contenu**
- **Commit**: `79c8012` - Correction des vulnérabilités CVE React Server Components
- **Commit**: `1db32dc` - Ajout de nouveaux exercices à la bibliothèque
- **Décision**: Priorisation de la sécurité avec mise à jour React
- **Impact**: Catalogue d'exercices élargi à 100+ exercices
- **Fichiers**: `frontend/package.json`, `backend/app/models/exercises.json`

**25 Décembre 2025 - UX et SEO**
- **Commits**:
  - `7cf0d3d` - Amélioration du SEO (schema.org, meta tags)
  - `dc16fe8` - Traduction français → anglais pour portée internationale
  - `61b6204` - Ajout popup lors du changement d'intensité
  - `8c48c0d` - Script de génération de vidéos locales
- **Décision**: Pivot vers un marché anglophone global
- **Impact SEO**: Intégration Schema.org (Organisation, WebApplication, FAQ)
- **Fichiers**: `frontend/app/page.tsx`, `frontend/app/layout.tsx`

**30 Décembre 2025 - Exercices Unilatéraux**
- **Commit**: `7c4c986` - Intégration de la logique des exercices unilatéraux
- **Décision Technique**: Support des exercices asymétriques (gauche/droite)
- **Impact**: Permet des workouts plus équilibrés musculairement
- **Fichiers**: `backend/app/models/exercise.py`, `backend/app/services/workout_generator.py`

---

#### **Janvier 2026 - Architecture Vidéo Avancée**

**03 Janvier 2026 - Upload et Mapping Vidéo**
- **Commits**:
  - `974abd2` - Changement de la logique de mapping d'URLs
  - `ca21653` - Logique d'upload de vidéos
- **Décision**: Migration vers Supabase Storage pour les vidéos d'exercices
- **Architecture**: CDN Supabase pour la distribution optimisée
- **Impact**: Réduction du temps de chargement via CDN global
- **Fichiers**: `backend/scripts/upload_trimmed_videos_to_supabase.py`

**03 Janvier 2026 - Système de Blocs (Block Structure)**
- **Commit**: `32ab95b` - Ajout logique de génération de sessions par blocs
- **Décision Majeure**: Adoption d'une structure par blocs thématiques
- **Blocs Implémentés**:
  - Upper Body (haut du corps)
  - Legs (jambes)
  - Cardio
  - Abs (abdos)
  - Finisher (exercice de fin intense)
- **Raison**: Structure pédagogique pour des workouts cohérents (minimum 10 minutes)
- **Documentation**: `/docs/workout_block_generation.md`
- **Fichiers**: `backend/app/models/config.py` (BlockConfig)

**14 Janvier 2026 - Optimisation Algorithme de Génération**
- **Commits**:
  - `d058ff8` - Amélioration de l'algorithme de génération
  - `23d25f3` - Génération de vidéos locales (développement hors ligne)
- **Décision**: Amélioration de la logique de sélection d'exercices
- **Optimisations**:
  - Filtrage intelligent par difficulté
  - Respect des contraintes no-jump
  - Distribution équilibrée des thèmes
- **Fichiers**: `backend/app/services/workout_generator.py`

**18-19 Janvier 2026 - Système d'Overlays Dynamiques**
- **Commit**: `e42d760` - Implémentation du système d'overlays dynamiques synchronisé avec la timeline vidéo
- **Décision Technique Majeure**: Architecture V2 des overlays
- **Architecture**:
  - **TimerRenderer**: Compte à rebours dynamique par exercice
  - **ProgressRenderer**: Barre de progression (X/Y exercices)
  - **DescriptionRenderer**: Nom de l'exercice
  - **BreakRenderer**: Overlays de pause avec countdown
- **Synchronisation**: Overlays alignés sur la timeline FFmpeg
- **Impact**: Expérience utilisateur professionnelle avec feedback visuel temps réel
- **Fichiers**:
  - `backend/video_studio/generators/workout_video_generator_v2.py`
  - `backend/video_studio/renderers/`
- **Documentation**: `/docs/workout_video_pregenerated_overlays_strategy.md`

**19 Janvier 2026 - Ajustements Overlays de Breaks**
- **Commits**:
  - `45d982d` - Correction du timing des overlays
  - `4ea142d` - Ajustement des overlays de pause
- **Décision**: Fine-tuning de la synchronisation overlay/vidéo
- **Impact**: Élimination des décalages audio/vidéo sur les breaks

**26-27 Janvier 2026 - Diagnostics et Stabilité**
- **Commits**:
  - `f19ce5b` - Gestion des logs FFmpeg longs pour éviter erreurs
  - `1feda50` - Outils de diagnostic pour le freeze de vidéos
- **Problème Identifié**: Freeze vidéo lors de génération longues
- **Solution**: Amélioration de la gestion de la mémoire et des logs FFmpeg
- **Fichiers**: `backend/app/services/video_service_optimized.py`

---

#### **Février 2026 - Optimisation Finale**

**31 Janvier 2026 - Corrections Déploiement**
- **Commit**: `c16acbc` - Fix déploiement Railway
- **Décision**: Configuration Nixpacks optimisée
- **Fichiers**: `railway.json`, `nixpacks.toml`

**02 Février 2026 - Performance Audio/Vidéo**
- **Commits**:
  - `e643cfa` - Correction erreur audio
  - `f9d6cb2` - **Décision Critique**: Élimination du ré-encodage et ajustement de vitesse
- **Décision Majeure**: Abandon de l'ajustement de vitesse basé sur l'intensité
- **Raison**:
  - Ré-encodage coûteux en temps et ressources
  - Problèmes de synchronisation audio/vidéo
  - Complexité FFmpeg excessive
- **Impact**:
  - **Gain de performance**: 40-50% de réduction du temps de génération
  - Élimination des problèmes audio
  - Simplification de la pipeline FFmpeg
- **Nouvelle Approche**: Utilisation de `stream copy` autant que possible
- **Fichiers**: `backend/app/services/video_service_optimized.py`

---

### Décisions Techniques Majeures

#### 1. **Architecture Vidéo**

**Problème Initial**: Génération vidéo lente (5-7 minutes pour 10 exercices)

**Solutions Implémentées** (chronologique):
1. **Cache des breaks** (Déc 2025) → Gain: 2-3s/pause
2. **Téléchargements parallèles** (Déc 2025) → Gain: 60-80%
3. **Overlays dynamiques** (Jan 2026) → UX professionnelle
4. **Abandon ré-encodage** (Fév 2026) → Gain: 40-50%

**Résultat Final**: 30-40 secondes pour un workout de 10 exercices (vs 5-7 minutes initialement)

#### 2. **Système de Blocs (Block Structure)**

**Date**: Janvier 2026

**Raison**: Workouts incohérents avec sélection aléatoire pure

**Solution**: Architecture par blocs thématiques répétables
- Garantit une progression logique
- Minimum 10 minutes de workout
- Distribution équilibrée des groupes musculaires

**Adoption**: Devenu standard pour toutes les générations auto

#### 3. **Migration Supabase Storage**

**Date**: Janvier 2026

**Raison**: Hébergement vidéo inefficace

**Bénéfices**:
- CDN global automatique
- Cache edge locations
- Réduction bande passante serveur backend
- URLs signées pour sécurité future

#### 4. **Overlays Dynamiques vs Pré-générés**

**Date**: Janvier 2026

**Décision**: Système hybride
- **Overlays dynamiques** (V2 actuel): Timer, progress, descriptions générés à la volée
- **Overlays pré-générés** (Planifié): Cache des overlays courants

**Raison**: Balance entre flexibilité et performance

#### 5. **Abandon de l'Ajustement de Vitesse**

**Date**: Février 2026

**Décision**: Retrait du feature `setpts` pour modifier la vitesse vidéo selon intensité

**Raison**:
- Complexité FFmpeg élevée
- Problèmes de synchronisation audio
- Temps de génération doublé par le ré-encodage

**Impact**: Simplification majeure de la pipeline, amélioration stabilité

---

### Évolution de la Stack Technique

| Composant | Initial | Actuel | Raison Changement |
|-----------|---------|--------|-------------------|
| **Overlays** | Statiques (images fixes) | Dynamiques (FFmpeg drawtext) | Flexibilité et temps réel |
| **Breaks** | Générés à la volée | Pré-générés (cache) | Performance (+2-3s/break) |
| **Storage Vidéos** | Local/serveur | Supabase Storage + CDN | Scalabilité et distribution |
| **Génération Workout** | Aléatoire pur | Blocs thématiques | Cohérence pédagogique |
| **Encodage** | Ré-encodage systématique | Stream copy prioritaire | Performance (+40-50%) |
| **Langue** | Français | Anglais | Marché international |
| **Frontend** | Next.js 15 | Next.js 16 + React 19 | Modernisation stack |

---

### Métriques de Performance (Évolution)

| Métrique | Déc 2025 | Jan 2026 | Fév 2026 | Objectif Phase 2 |
|----------|----------|----------|----------|------------------|
| **Temps génération (10 ex)** | 5-7 min | 1-2 min | 30-40s | 15-20s |
| **Taille catalogue** | 50 ex | 80 ex | 100+ ex | 200+ ex |
| **Taux cache hits** | 0% | 40% | 70% | 90% |
| **Temps premier byte** | 8-12s | 5-8s | 3-5s | <3s |
| **Qualité vidéo (CRF)** | 18 | 23 | 23 | 23 |

---

### Leçons Apprises

#### **1. Simplicité > Complexité**
- L'abandon de l'ajustement de vitesse a **amélioré** l'expérience utilisateur
- Moins de code = moins de bugs = meilleure maintenance

#### **2. Cache Early, Cache Often**
- Le cache des breaks a été l'optimisation la plus rapide à implémenter et la plus impactante
- ROI immédiat sur les assets répétitifs

#### **3. Streaming > Génération Complète**
- Permettre le streaming progressif réduit le temps perçu par l'utilisateur
- L'utilisateur peut commencer à voir la vidéo pendant qu'elle se génère encore

#### **4. Documentation Continue**
- Les fichiers `/docs/*.md` ont permis de maintenir la cohérence architecturale
- Facilite l'onboarding et les décisions futures

#### **5. Performance Monitoring**
- Les logs de profilage ont révélé les véritables goulots d'étranglement
- Mesurer avant d'optimiser (benchmark-driven development)

---

### Roadmap Technique (Next Steps)

#### **Q1 2026 (En cours)**
- ✅ Élimination du ré-encodage (Complété)
- 🔄 Implémentation cache overlays pré-générés (En cours)
- 📋 Parallélisation du traitement d'exercices (Planifié)

#### **Q2 2026**
- Authentication Supabase (OAuth + Email)
- Subscription Stripe (Freemium → Premium)
- Workout history tracking
- Advanced analytics

#### **Q3 2026**
- Mobile app (React Native)
- Offline workout downloads
- AI-powered recommendations
- Community features

---

### Problèmes Connus et Solutions

#### **Freeze Vidéo sur Workouts Longs (>20 exercices)**
- **Détecté**: Janvier 2026
- **Cause**: Mémoire FFmpeg saturée
- **Solution Actuelle**: Gestion logs FFmpeg + nettoyage progressif
- **Solution Future**: Split en segments + concat finale

#### **Synchronisation Audio/Vidéo**
- **Détecté**: Février 2026
- **Cause**: Ajustement vitesse avec `setpts`
- **Solution**: Abandon feature, utilisation stream copy
- **Statut**: ✅ Résolu

#### **Temps de Chargement Initiaux CDN**
- **Détecté**: Janvier 2026
- **Cause**: Cold start Supabase CDN
- **Solution Actuelle**: Pre-warming cache des exercices populaires
- **Impact**: Minime (<1s différence)

---

## Future Enhancements

### Phase 2 (Planned)
- User authentication with Supabase
- Premium exercise library
- Workout history tracking
- Personal goals and preferences
- Favorite exercises
- Stripe payment integration

### Phase 3 (Roadmap)
- AI-powered workout recommendation
- Social features (share workouts)
- Advanced analytics
- Mobile app (React Native)
- Offline workout downloads
- Community workouts

---

## Support & Documentation

- **Main Docs**: `/docs/architecture_globale.md`
- **Database**: `/docs/database_schema_diagram.md`
- **API**: `/docs/api_documentation.md`
- **Video Pipeline**: `/docs/workout_video_optimization_guide.md`
- **Block Generation**: `/docs/workout_block_generation.md`

---

**Last Updated**: 2026-02-02
**Version**: 1.0.0
**Maintainer**: Virtual AI Coach Team
