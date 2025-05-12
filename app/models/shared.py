from enum import Enum

class UserType(str, Enum):
    CANDIDATE = "candidate"
    EMPLOYER = "employer"
    ADMIN = "admin"

class ProfileStatus(str, Enum):
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    DELETED = "deleted"
    PENDING = "pending"
    SUSPENDED = "suspended"
    INCOMPLETE = "incomplete"
    VERIFIED = "verified"
    ARCHIVED = "archived"


class ApplicationStatus(str, Enum):
    INACTIVE = "inactive"           # Covers DEACTIVATED, DELETED, ARCHIVED
    PROFILE_INCOMPLETE = "profile_incomplete"
    PROFILE_PENDING = "profile_pending_verification"
    PROFILE_VERIFIED = "profile_verified"
    PROFILE_SUSPENDED = "profile_suspended"

    APPLICATION_PENDING = "application_pending"
    APPLICATION_VIEWED = "application_viewed"
    APPLICATION_ACCEPTED = "application_accepted"
    APPLICATION_DECLINED = "application_declined"
    INTERVIEW_STAGE = "interview_stage"
    OFFER_EXTENDED = "offer_extended"
    APPLICATION_REJECTED = "application_rejected"
    CANDIDATE_HIRED = "candidate_hired"
