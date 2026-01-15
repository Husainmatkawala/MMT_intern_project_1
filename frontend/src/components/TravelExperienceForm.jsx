import { useState } from 'react'
import { FiX, FiCheck, FiMapPin, FiInfo, FiStar, FiAward, FiGift } from 'react-icons/fi'

const TravelExperienceForm = () => {
  const [formData, setFormData] = useState({
    title: '',
    destination: '',
    travelDate: '',
    overallExperience: '',
  })

  const [errors, setErrors] = useState({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitSuccess, setSubmitSuccess] = useState(false)

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }))
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  const validateForm = () => {
    const newErrors = {}

    if (!formData.title.trim()) newErrors.title = 'Title is required'
    if (!formData.destination.trim()) newErrors.destination = 'Destination is required'
    if (!formData.travelDate) newErrors.travelDate = 'Travel date is required'
    if (!formData.overallExperience.trim()) newErrors.overallExperience = 'Overall experience is required'

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setIsSubmitting(true)

    // Simulate API call
    setTimeout(() => {
      setIsSubmitting(false)
      setSubmitSuccess(true)
      // Reset form after 3 seconds
      setTimeout(() => {
        setFormData({
          title: '',
          destination: '',
          travelDate: '',
          overallExperience: '',
        })
        setSubmitSuccess(false)
      }, 3000)
    }, 2000)
  }

  if (submitSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 animate-fade-in">
        <div className="section-card max-w-md w-full text-center animate-slide-up">
          <div className="relative w-20 h-20 mx-auto mb-6">
            <div className="absolute inset-0 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full animate-pulse-slow"></div>
            <div className="absolute inset-2 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
              <FiCheck className="w-10 h-10 text-green-600 dark:text-green-400" />
            </div>
          </div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 dark:from-primary-400 dark:to-purple-400 bg-clip-text text-transparent mb-3">
            Experience Submitted!
          </h2>
          <p className="text-gray-600 dark:text-gray-300 mb-6 leading-relaxed">
            Your travel experience has been submitted successfully. Our team will verify your submission and you'll receive rewards based on the quality of your experience.
          </p>
          <div className="flex items-center justify-center gap-2 text-primary-600 dark:text-primary-400 font-semibold">
            <FiAward className="w-5 h-5" />
            <span>Earn points, vouchers, and badges for verified experiences!</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen py-8 px-4 animate-fade-in">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10 animate-slide-up">
          <div className="inline-block mb-6">
            <div className="flex items-center justify-center">
              {/* MakeMyTrip Logo */}
              {/* Option 1: If you have the logo image file, uncomment and update the import at the top */}
              {/* <img 
                src={makemytripLogo} 
                alt="MakeMyTrip" 
                className="h-12 md:h-16 w-auto"
              /> */}
              
              {/* Option 2: If logo is in public folder, use this */}
              <img 
                src="/makemytrip-logo.png" 
                alt="MakeMyTrip" 
                className="h-12 md:h-16 w-auto"
                onError={(e) => {
                  // Fallback to CSS logo if image not found
                  e.target.style.display = 'none'
                  const fallback = e.target.nextElementSibling
                  if (fallback) fallback.style.display = 'flex'
                }}
              />
              
              {/* Fallback CSS Logo (shown if image fails to load) */}
              <div className="flex items-baseline gap-0" style={{ display: 'none' }}>
                {/* "make" - dark blue */}
                <span className="text-4xl md:text-5xl font-bold text-blue-900 dark:text-blue-700 lowercase" style={{ fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif', letterSpacing: '-0.02em' }}>
                  make
                </span>
                {/* "my" - white text in red rounded rectangle */}
                <div className="mx-1.5 bg-red-600 dark:bg-red-500 rounded-lg px-2.5 py-0.5 flex items-center justify-center" style={{ height: '1.3em', verticalAlign: 'baseline' }}>
                  <span className="text-4xl md:text-5xl font-bold text-white lowercase relative" style={{ fontFamily: '"Brush Script MT", "Lucida Handwriting", cursive, sans-serif', lineHeight: '1', transform: 'scaleY(1.15)' }}>
                    my
                  </span>
                </div>
                {/* "trip" - dark blue */}
                <span className="text-4xl md:text-5xl font-bold text-blue-900 dark:text-blue-700 lowercase" style={{ fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif', letterSpacing: '-0.02em' }}>
                  trip
                </span>
              </div>
            </div>
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold mb-4 bg-gradient-to-r from-primary-600 via-purple-600 to-pink-600 dark:from-primary-400 dark:via-purple-400 dark:to-pink-400 bg-clip-text text-transparent">
            Share Your Travel Experience
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-6">
            Help fellow travelers and earn rewards for verified experiences
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <span className="badge">
              <FiStar className="w-4 h-4" /> Earn Points
            </span>
            <span className="badge">
              <FiGift className="w-4 h-4" /> Get Vouchers
            </span>
            <span className="badge">
              <FiAward className="w-4 h-4" /> Unlock Badges
            </span>
          </div>
        </div>

        {/* Main Form */}
        <form onSubmit={handleSubmit} className="section-card space-y-10 animate-slide-up">
          {/* Basic Information */}
          <section className="border-b border-gray-200 dark:border-gray-700 pb-8">
            <h2 className="section-header">
              <span className="text-2xl">📋</span>
              Basic Information
            </h2>
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                  Experience Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  placeholder="e.g., Amazing 5-day trip to Goa"
                  className={`form-input ${errors.title ? 'border-red-500 dark:border-red-500 ring-red-500' : ''}`}
                />
                {errors.title && <p className="text-red-500 dark:text-red-400 text-sm mt-2 flex items-center gap-1">
                  <FiX className="w-4 h-4" /> {errors.title}
                </p>}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                    <FiMapPin className="inline mr-2 text-primary-600 dark:text-primary-400" /> Destination <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.destination}
                    onChange={(e) => handleInputChange('destination', e.target.value)}
                    placeholder="City, Country"
                    className={`form-input ${errors.destination ? 'border-red-500 dark:border-red-500 ring-red-500' : ''}`}
                  />
                  {errors.destination && <p className="text-red-500 dark:text-red-400 text-sm mt-2 flex items-center gap-1">
                    <FiX className="w-4 h-4" /> {errors.destination}
                  </p>}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                    Travel Date <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={formData.travelDate}
                    onChange={(e) => handleInputChange('travelDate', e.target.value)}
                    className={`form-input ${errors.travelDate ? 'border-red-500 dark:border-red-500 ring-red-500' : ''}`}
                  />
                  {errors.travelDate && <p className="text-red-500 dark:text-red-400 text-sm mt-2 flex items-center gap-1">
                    <FiX className="w-4 h-4" /> {errors.travelDate}
                  </p>}
                </div>
              </div>
            </div>
          </section>

          {/* Overall Experience */}
          <section className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                Overall Experience <span className="text-red-500">*</span> <span className="text-gray-500 dark:text-gray-400 font-normal">(Your main review)</span>
              </label>
              <textarea
                value={formData.overallExperience}
                onChange={(e) => handleInputChange('overallExperience', e.target.value)}
                placeholder="Write a comprehensive review of your overall travel experience. Share details about hotels, attractions, food, local commute, costs, safety, tips, and anything else that would help fellow travelers..."
                rows="12"
                className={`form-textarea ${errors.overallExperience ? 'border-red-500 dark:border-red-500 ring-red-500' : ''}`}
              />
              {errors.overallExperience && <p className="text-red-500 dark:text-red-400 text-sm mt-2 flex items-center gap-1">
                <FiX className="w-4 h-4" /> {errors.overallExperience}
              </p>}
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 flex items-center gap-1">
                <FiInfo className="w-3 h-3" /> The more detailed your experience, the higher your reward points!
              </p>
            </div>
          </section>

          {/* Submit Button */}
          <div className="flex flex-col sm:flex-row gap-4 pt-6">
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary flex-1 text-lg"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Submitting...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <FiCheck className="w-5 h-5" /> Submit Experience
                </span>
              )}
            </button>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="btn-secondary text-lg"
            >
              Reset Form
            </button>
          </div>

          {/* Info Box */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-5 mt-8">
            <p className="text-sm text-blue-800 dark:text-blue-300 leading-relaxed">
              <strong className="font-semibold">💡 Note:</strong> Your submission will be verified through AI classifiers for authenticity. 
              Verified experiences earn higher rewards including points, vouchers, and exclusive badges.
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}

export default TravelExperienceForm
