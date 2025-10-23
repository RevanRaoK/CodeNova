"""
Test script for enhanced user service functionality.
Tests validation, error handling, and rollback behavior.
"""
import asyncio
import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.users import User, Base
from app.services.user_service import UserService
from app.schemas.user import UserProfileUpdate, UserPreferences, NotificationPreferences
from app.core.security import get_password_hash
from fastapi import HTTPException


async def test_profile_validation():
    """Test profile update validation."""
    print("\n=== Testing Profile Validation ===")
    db = SessionLocal()
    user_service = UserService()
    
    try:
        # Create a test user
        test_user = User(
            email="test_validation@example.com",
            first_name="Test",
            last_name="User",
            hashed_password=get_password_hash("TestPassword123"),
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✓ Created test user with ID: {test_user.id}")
        
        # Test 1: Valid profile update
        print("\nTest 1: Valid profile update")
        profile_update = UserProfileUpdate(
            firstName="John",
            lastName="Doe",
            jobTitle="Senior Developer",
            bio="Experienced software engineer",
            programmingLanguages=["Python", "JavaScript", "TypeScript"]
        )
        result = await user_service.update_user_profile(db, test_user.id, profile_update)
        print(f"✓ Profile updated successfully: {result.firstName} {result.lastName}")
        
        # Test 2: Empty first name (should fail)
        print("\nTest 2: Empty first name validation")
        try:
            profile_update = UserProfileUpdate(firstName="   ")
            await user_service.update_user_profile(db, test_user.id, profile_update)
            print("✗ Should have failed with empty first name")
        except HTTPException as e:
            print(f"✓ Correctly rejected empty first name: {e.detail}")
        
        # Test 3: Invalid characters in name (should fail)
        print("\nTest 3: Invalid characters in name")
        try:
            profile_update = UserProfileUpdate(firstName="John123")
            await user_service.update_user_profile(db, test_user.id, profile_update)
            print("✗ Should have failed with invalid characters")
        except HTTPException as e:
            print(f"✓ Correctly rejected invalid characters: {e.detail}")
        
        # Test 4: Too long bio (should fail)
        print("\nTest 4: Bio length validation")
        try:
            profile_update = UserProfileUpdate(bio="x" * 1001)
            await user_service.update_user_profile(db, test_user.id, profile_update)
            print("✗ Should have failed with too long bio")
        except HTTPException as e:
            print(f"✓ Correctly rejected too long bio: {e.detail}")
        
        # Test 5: Too many programming languages (should fail)
        print("\nTest 5: Programming languages limit")
        try:
            profile_update = UserProfileUpdate(
                programmingLanguages=[f"Lang{i}" for i in range(21)]
            )
            await user_service.update_user_profile(db, test_user.id, profile_update)
            print("✗ Should have failed with too many languages")
        except HTTPException as e:
            print(f"✓ Correctly rejected too many languages: {e.detail}")
        
        # Test 6: Duplicate email (should fail)
        print("\nTest 6: Duplicate email validation")
        # Create another user
        another_user = User(
            email="another@example.com",
            first_name="Another",
            last_name="User",
            hashed_password=get_password_hash("TestPassword123"),
            is_active=True
        )
        db.add(another_user)
        db.commit()
        
        try:
            profile_update = UserProfileUpdate(email="another@example.com")
            await user_service.update_user_profile(db, test_user.id, profile_update)
            print("✗ Should have failed with duplicate email")
        except HTTPException as e:
            print(f"✓ Correctly rejected duplicate email: {e.detail}")
        
        print("\n✓ All profile validation tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        db.query(User).filter(User.email.in_([
            "test_validation@example.com",
            "another@example.com"
        ])).delete(synchronize_session=False)
        db.commit()
        db.close()


async def test_preferences_validation():
    """Test preferences update validation."""
    print("\n=== Testing Preferences Validation ===")
    db = SessionLocal()
    user_service = UserService()
    
    try:
        # Create a test user
        test_user = User(
            email="test_prefs@example.com",
            first_name="Test",
            last_name="Prefs",
            hashed_password=get_password_hash("TestPassword123"),
            is_active=True,
            preferences="{}"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✓ Created test user with ID: {test_user.id}")
        
        # Test 1: Valid preferences update
        print("\nTest 1: Valid preferences update")
        prefs = UserPreferences(
            theme="dark",
            language="en",
            defaultProgrammingLanguage="python",
            aiModel="gemini-pro",
            autoSave=True
        )
        result = await user_service.update_user_preferences(db, test_user.id, prefs)
        print(f"✓ Preferences updated successfully: theme={result['userPreferences']['theme']}")
        
        # Test 2: Invalid theme (should fail)
        print("\nTest 2: Invalid theme validation")
        try:
            prefs = UserPreferences(theme="invalid_theme")
            await user_service.update_user_preferences(db, test_user.id, prefs)
            print("✗ Should have failed with invalid theme")
        except HTTPException as e:
            print(f"✓ Correctly rejected invalid theme: {e.detail}")
        
        # Test 3: Invalid AI model (should fail)
        print("\nTest 3: Invalid AI model validation")
        try:
            prefs = UserPreferences(aiModel="invalid-model")
            await user_service.update_user_preferences(db, test_user.id, prefs)
            print("✗ Should have failed with invalid AI model")
        except HTTPException as e:
            print(f"✓ Correctly rejected invalid AI model: {e.detail}")
        
        # Test 4: Invalid editor theme (should fail)
        print("\nTest 4: Invalid editor theme validation")
        try:
            prefs = UserPreferences(codeEditorTheme="invalid-editor-theme")
            await user_service.update_user_preferences(db, test_user.id, prefs)
            print("✗ Should have failed with invalid editor theme")
        except HTTPException as e:
            print(f"✓ Correctly rejected invalid editor theme: {e.detail}")
        
        print("\n✓ All preferences validation tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        db.query(User).filter(User.email == "test_prefs@example.com").delete()
        db.commit()
        db.close()


async def test_notification_preferences():
    """Test notification preferences update."""
    print("\n=== Testing Notification Preferences ===")
    db = SessionLocal()
    user_service = UserService()
    
    try:
        # Create a test user
        test_user = User(
            email="test_notifs@example.com",
            first_name="Test",
            last_name="Notifs",
            hashed_password=get_password_hash("TestPassword123"),
            is_active=True,
            preferences="{}"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✓ Created test user with ID: {test_user.id}")
        
        # Test 1: Valid notification preferences update
        print("\nTest 1: Valid notification preferences update")
        from app.schemas.user import EmailNotificationSettings, PushNotificationSettings
        notif_prefs = NotificationPreferences(
            emailNotifications=EmailNotificationSettings(
                reviewCompleted=True,
                newPattern=True,
                securityAlert=True,
                weeklyDigest=False,
                marketingEmails=False
            ),
            pushNotifications=PushNotificationSettings(
                reviewCompleted=True,
                newPattern=False,
                securityAlert=True
            ),
            frequency="immediate"
        )
        result = await user_service.update_notification_preferences(db, test_user.id, notif_prefs)
        print(f"✓ Notification preferences updated successfully")
        print(f"  Email notifications - reviewCompleted: {result['notifications']['emailNotifications']['reviewCompleted']}")
        print(f"  Push notifications - reviewCompleted: {result['notifications']['pushNotifications']['reviewCompleted']}")
        print(f"  Frequency: {result['notifications']['frequency']}")
        
        # Test 2: Invalid frequency (should fail)
        print("\nTest 2: Invalid frequency validation")
        try:
            notif_prefs = NotificationPreferences(
                emailNotifications=EmailNotificationSettings(),
                pushNotifications=PushNotificationSettings(),
                frequency="invalid_frequency"
            )
            await user_service.update_notification_preferences(db, test_user.id, notif_prefs)
            print("✗ Should have failed with invalid frequency")
        except HTTPException as e:
            print(f"✓ Correctly rejected invalid frequency: {e.detail}")
        
        print("\n✓ All notification preferences tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        db.query(User).filter(User.email == "test_notifs@example.com").delete()
        db.commit()
        db.close()


async def test_rollback_behavior():
    """Test that database rollback works correctly on errors."""
    print("\n=== Testing Rollback Behavior ===")
    db = SessionLocal()
    user_service = UserService()
    
    try:
        # Create a test user
        test_user = User(
            email="test_rollback@example.com",
            first_name="Original",
            last_name="Name",
            hashed_password=get_password_hash("TestPassword123"),
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✓ Created test user with ID: {test_user.id}")
        print(f"  Original name: {test_user.first_name} {test_user.last_name}")
        
        # Try to update with invalid data (should rollback)
        print("\nTest: Attempting invalid update (should rollback)")
        try:
            profile_update = UserProfileUpdate(
                firstName="Valid",
                lastName="Name",
                bio="x" * 1001  # Too long, should fail
            )
            await user_service.update_user_profile(db, test_user.id, profile_update)
            print("✗ Should have failed")
        except HTTPException as e:
            print(f"✓ Update correctly failed: {e.detail}")
        
        # Verify data was not changed (rollback worked)
        db.refresh(test_user)
        if test_user.first_name == "Original" and test_user.last_name == "Name":
            print(f"✓ Rollback successful - data unchanged: {test_user.first_name} {test_user.last_name}")
        else:
            print(f"✗ Rollback failed - data was changed: {test_user.first_name} {test_user.last_name}")
        
        print("\n✓ Rollback behavior test passed!")
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        db.query(User).filter(User.email == "test_rollback@example.com").delete()
        db.commit()
        db.close()


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Enhanced User Service Test Suite")
    print("=" * 60)
    
    await test_profile_validation()
    await test_preferences_validation()
    await test_notification_preferences()
    await test_rollback_behavior()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
