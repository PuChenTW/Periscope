"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { User, Save, Trash2, AlertTriangle } from "lucide-react"

export function AccountSettings() {
  const [email, setEmail] = useState("john@example.com")
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")

  const handleSaveProfile = () => {
    // Save profile logic here
    console.log("Saving profile...")
  }

  const handleChangePassword = () => {
    // Change password logic here
    console.log("Changing password...")
  }

  const handleDeleteAccount = () => {
    // Delete account logic here
    console.log("Deleting account...")
  }

  return (
    <Card id="account">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="w-5 h-5" />
          Account Settings
        </CardTitle>
        <CardDescription>Manage your account information and security settings</CardDescription>
      </CardHeader>
      <CardContent className="space-y-8">
        {/* Profile Information */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Profile Information</h3>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
              <p className="text-xs text-muted-foreground">
                Changing your email will require verification of the new address
              </p>
            </div>
          </div>
          <Button onClick={handleSaveProfile}>
            <Save className="w-4 h-4 mr-2" />
            Save Profile
          </Button>
        </div>

        <Separator />

        {/* Change Password */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Change Password</h3>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="current-password">Current Password</Label>
              <Input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-password">New Password</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm New Password</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
          </div>
          <Button onClick={handleChangePassword} disabled={!currentPassword || !newPassword || !confirmPassword}>
            <Save className="w-4 h-4 mr-2" />
            Change Password
          </Button>
        </div>

        <Separator />

        {/* Danger Zone */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-destructive">Danger Zone</h3>
          <div className="p-4 border border-destructive/20 rounded-lg bg-destructive/5">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-medium text-destructive">Delete Account</h4>
                <p className="text-sm text-muted-foreground mt-1">
                  Permanently delete your account and all associated data. This action cannot be undone.
                </p>
                <Button variant="destructive" size="sm" className="mt-3" onClick={handleDeleteAccount}>
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Account
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
