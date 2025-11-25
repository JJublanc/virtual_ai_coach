'use client'

import Image from "next/image"
import Link from "next/link"
import { Play, Zap, Target, Clock, Dumbbell, TrendingUp } from "lucide-react"

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-green-500 to-green-600 text-white">
        <div className="absolute inset-0 bg-black/10" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 sm:py-32">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight mb-6">
              Your Personal
              <span className="block text-green-200">Virtual Sports Coach</span>
            </h1>
            <p className="text-xl sm:text-2xl text-green-50 mb-8 max-w-3xl mx-auto">
              Personalized workouts with guided videos, adapted to your level and goals
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/train"
                className="inline-flex items-center justify-center gap-2 bg-white text-green-600 px-8 py-4 rounded-full text-lg font-semibold hover:bg-green-50 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                <Play className="w-6 h-6" fill="currentColor" />
                Start Training
              </Link>
              <Link
                href="/train"
                className="inline-flex items-center justify-center gap-2 bg-green-700 text-white px-8 py-4 rounded-full text-lg font-semibold hover:bg-green-800 transition-all border-2 border-white/20"
              >
                Discover Features
              </Link>
            </div>
          </div>
        </div>
        {/* Decorative wave */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 120L60 110C120 100 240 80 360 70C480 60 600 60 720 65C840 70 960 80 1080 85C1200 90 1320 90 1380 90L1440 90V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z" fill="rgb(249, 250, 251)"/>
          </svg>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Why choose our virtual coach?
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            A complete and personalized training experience
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow">
            <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mb-6">
              <Play className="w-7 h-7 text-green-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Guided Videos
            </h3>
            <p className="text-gray-600">
              Follow video exercises with clear instructions and an integrated timer for each movement
            </p>
          </div>

          {/* Feature 2 */}
          <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow">
            <div className="w-14 h-14 bg-blue-100 rounded-full flex items-center justify-center mb-6">
              <Zap className="w-7 h-7 text-blue-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Quick Customization
            </h3>
            <p className="text-gray-600">
              Choose your intensity (low, medium, high) and instantly generate your workout session
            </p>
          </div>

          {/* Feature 3 */}
          <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow">
            <div className="w-14 h-14 bg-purple-100 rounded-full flex items-center justify-center mb-6">
              <Target className="w-7 h-7 text-purple-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Advanced Options
            </h3>
            <p className="text-gray-600">
              Exclude jumping exercises, avoid repetitions, and customize your work/rest intervals
            </p>
          </div>

          {/* Feature 4 */}
          <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow">
            <div className="w-14 h-14 bg-orange-100 rounded-full flex items-center justify-center mb-6">
              <Clock className="w-7 h-7 text-orange-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Time Management
            </h3>
            <p className="text-gray-600">
              Visualize your progress in real-time with a circular timer and progress bar
            </p>
          </div>

          {/* Feature 5 */}
          <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow">
            <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mb-6">
              <Dumbbell className="w-7 h-7 text-red-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Exercise Variety
            </h3>
            <p className="text-gray-600">
              Access a complete library of cardio, strength, and flexibility exercises
            </p>
          </div>

          {/* Feature 6 */}
          <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow">
            <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mb-6">
              <TrendingUp className="w-7 h-7 text-green-600" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Progress Tracking
            </h3>
            <p className="text-gray-600">
              Track your exercise sequence with clear numbering and visual indicators
            </p>
          </div>
        </div>
      </section>

      {/* How it works Section */}
      <section className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              How does it work?
            </h2>
            <p className="text-xl text-gray-600">
              Three simple steps to get started
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-500 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                1
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">
                Configure Your Session
              </h3>
              <p className="text-gray-600">
                Choose your intensity and exercise preferences with just a few clicks
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-500 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                2
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">
                Generate Your Workout
              </h3>
              <p className="text-gray-600">
                Our system automatically creates a personalized video with all your exercises
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-500 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-6">
                3
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">
                Train!
              </h3>
              <p className="text-gray-600">
                Follow the guided video with timer and descriptions for each exercise
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-br from-green-500 to-green-600 text-white py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Ready to transform your fitness routine?
          </h2>
          <p className="text-xl text-green-50 mb-8">
            Start your first personalized training session now
          </p>
          <Link
            href="/train"
            className="inline-flex items-center justify-center gap-2 bg-white text-green-600 px-10 py-5 rounded-full text-lg font-semibold hover:bg-green-50 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Play className="w-6 h-6" fill="currentColor" />
            Start Now
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-sm">
              © 2024 Virtual AI Coach. Your partner for personalized training.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
